// Read-only client for the arena server. Every number shown in the SOC comes from these
// endpoints, which parse recorded match event logs. There are no fabricated fallbacks here:
// a failed request surfaces as an error so the UI can say "no data" honestly.

export interface DashboardStats {
  total_battles: number;
  red_success_rate: number;
  blue_defense_rate: number;
  vulnerabilities_discovered: number;
  vulnerabilities_patched: number;
  failed_patch_attempts: number;
  average_patch_time_sec: number;
  application_availability: string;
  charts: {
    comparison: Array<{ metric: string; red: number; blue: number }>;
    timeline: Array<{ time: string; attacks: number; defenses: number; health: number }>;
    event_distribution: Array<{ name: string; count: number; color: string }>;
  };
  recent_battles: Battle[];
}

export interface Battle {
  id: string;
  name: string;
  description: string;
  status: string;
  target_environment: string;
  red_model: string;
  blue_model: string;
  simulation_mode: string;
  selected_vulnerabilities: string[];
  max_execution_time: number;
  max_test_requests: number;
  auto_deploy: number;
  start_time: string;
  end_time?: string;
  duration_seconds: number;
  red_discoveries: number;
  red_flags_captured: number;
  blue_patches_generated: number;
  blue_patches_approved: number;
  blue_patches_rejected: number;
  final_health: string;
  outcome: string;
  sweep_requests: number;
  sweep_findings: number;
  llm_calls: number | null;  // null on logs recorded before per-call counts existed
  red_llm_calls: number | null;  // null when the split was not recorded and cannot be inferred
  blue_llm_calls: number | null;
  red_tokens: number | null;
  blue_tokens: number | null;
  cache_hits: number;
  tokens_used: number;
  replay: string;
}

export interface BattleEvent {
  timestamp: string;
  ts?: number;
  source: 'RED' | 'BLUE' | 'REFEREE' | 'ARENA';
  event_type: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  endpoint?: string;
  vuln_type?: string;
  summary: string;
  details?: any;
}

export interface Vulnerability {
  id: string;
  name: string;
  severity: string;
  cwe: string;
  cvss: number;
  affected_endpoint: string;
  source_file: string;
  description: string;
  root_cause: string;
  security_impact: string;
  detection_evidence: string;
  mitigation: string;
  before_patch: string;
  after_patch: string;
  match_id: string;
  patched: boolean;
}

export interface PatchRecord {
  id: string;
  vuln_type: string;
  name: string;
  source_file: string;
  original_code: string;
  proposed_patch: string;
  diff_code: string;
  explanation: string;
  status: 'approved' | 'pending' | 'rejected';
  functional_passed: boolean;
  security_passed: boolean;
  health_passed: boolean;
  referee_notes: string;
  match_id: string;
}

export interface ReportFinding {
  vuln_type: string;
  endpoint: string;
  canary_token: string;
  status: 'Mitigated' | 'Open';
  patch_verification: string;
  functional_tests: string;
  security_tests: string;
}

export interface BattleReport {
  report_id: string;
  generated_at: string;
  battle: {
    id: string;
    name: string;
    outcome: string;
    duration_seconds: number;
    red_flags_captured: number;
    red_discoveries: number;
    blue_patches_generated: number;
    blue_patches_approved: number;
    final_health: string;
  };
  executive_summary: { title: string; target_app: string; source: string };
  findings: ReportFinding[];
}

export interface TargetStatus {
  status: 'operational' | 'idle';
  global_mode: 'secure' | 'vulnerable';
  app_dir: string;
  admin_routes: string[];
  loot_paths: string[];
  flag_owners: Record<string, string>;
  strategy: string;
  patches: Record<string, boolean>;
  note: string;
}

export interface TargetLive {
  url: string | null;
  port: number | null;
  alive: boolean;
  match_id: string | null;
  running: boolean;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(`${path} failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export const getDashboardStats = () => get<DashboardStats>('/api/dashboard/stats');
export const getBattles = () => get<Battle[]>('/api/battles');
export const getBattle = (id: string) => get<Battle>(`/api/battles/${encodeURIComponent(id)}`);
export const getBattleReport = (id: string) =>
  get<BattleReport>(`/api/battles/${encodeURIComponent(id)}/report`);
export const getVulnerabilities = () => get<Vulnerability[]>('/api/vulnerabilities');
export const getPatches = () => get<PatchRecord[]>('/api/patches');
export const getTargetConfig = () => get<TargetStatus>('/api/target/config/status');
export const getTargetLive = () => get<TargetLive>('/api/target/live');
export const getCurrentMatch = () => get<{ match_id: string | null; running: boolean }>('/api/match/current');

export async function startMatch(): Promise<string> {
  const res = await fetch('/api/match/start', { method: 'POST' });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return (await res.json()).match_id;
}

function normalizeEvent(data: any): BattleEvent {
  const base = {
    timestamp: new Date().toISOString(),
    ts: typeof data.ts === 'number' ? data.ts : undefined,
    details: data,
  };
  switch (data.type) {
    case 'match_start':
      return {
        ...base, source: 'ARENA', event_type: 'MATCH_STARTED', severity: 'info',
        summary: `Match initialized (${data.strategy || 'hybrid'} strategy). ${data.routes?.length ?? 0} target routes discovered for testing.`,
      };
    case 'health':
      return {
        ...base, source: 'REFEREE', event_type: 'HEALTH_CHECK', severity: 'success',
        summary: `Functional test suite: ${data.passed ?? 0} passed, ${data.failed ?? 0} failed.`,
      };
    case 'sweep_start':
      return {
        ...base, source: 'RED', event_type: 'SWEEP_STARTED', severity: 'info',
        summary: 'Deterministic template sweep started across query, ID, admin and path vectors.',
      };
    case 'sweep_done':
      return {
        ...base, source: 'RED', event_type: 'SWEEP_FINISHED', severity: 'info',
        summary: `Sweep finished: ${data.findings ?? 0} findings from ${data.requests ?? 0} bounded requests.`,
      };
    case 'red_action': {
      const args = data.args || {};
      return {
        ...base, source: 'RED', event_type: 'SECURITY_TEST', severity: 'warning',
        endpoint: args.path || data.route,
        summary: `${data.source === 'sweep' ? 'Template sweep' : 'Red agent'} ${data.tool}` +
          `${args.method ? ` ${args.method}` : ''}${args.path ? ` ${args.path}` : ''}` +
          `${data.status ? ` -> HTTP ${data.status}` : ''}`,
      };
    }
    case 'red_error':
      return {
        ...base, source: 'RED', event_type: 'PROBE_ERROR', severity: 'warning',
        summary: `${data.tool || 'Red'} error: ${data.error}`,
      };
    case 'breach':
      return {
        ...base, source: 'RED', event_type: 'CANARY_CAPTURED', severity: 'error',
        endpoint: data.route, vuln_type: data.vuln_class,
        summary: `Breach on ${data.method || 'GET'} ${data.path || data.route}: ` +
          `${data.vuln_class} leaked ${data.flag}.`,
      };
    case 'blue_thinking':
      return {
        ...base, source: 'BLUE', event_type: 'ROOT_CAUSE_ANALYSIS', severity: 'info',
        summary: data.text || `Analyzing the ${data.vuln_class || ''} finding and drafting a minimal fix.`,
      };
    case 'blue_attempt':
      return {
        ...base, source: 'BLUE', event_type: 'PATCH_ATTEMPT', severity: data.ok ? 'info' : 'warning',
        summary: `Patch attempt ${data.n ?? ''}: ${data.ok ? 'applied' : 'rejected'}${data.reason ? ` (${data.reason})` : ''}.`,
      };
    case 'blue_cache':
      return {
        ...base, source: 'BLUE', event_type: 'PATCH_CACHE', severity: 'info',
        summary: data.text || `Patch cache ${data.hit ? 'hit' : 'miss'} for ${data.vuln_class || 'finding'}.`,
      };
    case 'blue_error':
      return {
        ...base, source: 'BLUE', event_type: 'BLUE_ERROR', severity: 'error',
        summary: `Blue agent error: ${data.error}`,
      };
    case 'patched':
      return {
        ...base, source: 'REFEREE', event_type: 'PATCH_APPROVED', severity: 'success',
        endpoint: data.route, vuln_type: data.vuln_class,
        summary: `Referee verified the patch on ${data.route} in ${data.ttp_seconds}s` +
          `${data.cached ? ' (replayed from cache)' : ''}: exploit blocked, functional tests pass.`,
      };
    case 'score':
      return {
        ...base, source: 'REFEREE', event_type: 'SCORE_UPDATE', severity: 'info',
        summary: `Score - Red: ${data.red} | Blue: ${data.blue}`,
      };
    case 'budget_exceeded':
      return {
        ...base, source: 'ARENA', event_type: 'BUDGET_EXCEEDED', severity: 'warning',
        summary: `Token budget exhausted: ${data.error || 'match stopped gracefully'}.`,
      };
    case 'match_end': {
      const s = data.summary || {};
      return {
        ...base, source: 'REFEREE', event_type: 'BATTLE_CONCLUDED', severity: 'success',
        summary: `Match concluded - findings ${s.red ?? 0}, patches ${s.blue ?? 0}, ` +
          `closed ${s.closed ?? 0}/${s.total ?? 0}.`,
      };
    }
    case 'idle':
      return {
        ...base, source: 'ARENA', event_type: 'IDLE', severity: 'info',
        summary: 'No match is running. Start a live match or replay a recorded log.',
      };
    default:
      return {
        ...base, source: 'ARENA', event_type: data.type || 'INFO', severity: 'info',
        summary: data.text || JSON.stringify(data),
      };
  }
}

// Opens the arena WebSocket through the dev-server proxy. Passing a recorded log replays it;
// otherwise the stream is whatever live match the server currently has.
export function connectBattleWS(
  replay: string | undefined,
  onMessage: (ev: BattleEvent) => void,
  onClose?: () => void,
): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const query = replay ? `?replay=${encodeURIComponent(replay)}&speed=1` : '';
  const ws = new WebSocket(`${protocol}//${window.location.host}/ws${query}`);
  ws.onmessage = (event) => {
    try {
      onMessage(normalizeEvent(JSON.parse(event.data)));
    } catch (e) {
      console.error('WS parse error', e);
    }
  };
  ws.onclose = () => onClose?.();
  return ws;
}
