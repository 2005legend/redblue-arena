import {createFileRoute} from '@tanstack/react-router';
import {CatalogPage} from '@/components/catalog-page';
import {pageHead} from '@/lib/catalog';
type Search={q?:string;category?:string;sort?:string};
export const Route=createFileRoute('/shop')({validateSearch:(s:Record<string,unknown>):Search=>({...(typeof s['q']==='string'?{q:s['q']}:{}),...(typeof s['category']==='string'?{category:s['category']}:{}),...(typeof s['sort']==='string'?{sort:s['sort']}: {})}),head:()=>pageHead('Shop All Products','Explore ShopSphere’s curated collection. Search, filter and discover your next everyday favorite.'),component:Shop});
function Shop(){const s=Route.useSearch();return <CatalogPage key={`${s.q}-${s.category}`} initialQuery={s.q??''} initialCategory={s.category??''} initialSort={s.sort??'featured'}/>}
