import {createFileRoute,Link} from '@tanstack/react-router';
import {Heart} from 'lucide-react';
import {useStore,ProductGrid} from '@/components/store-shell';
import {Button} from '@/components/ui/button';
import {products,pageHead} from '@/lib/catalog';
export const Route=createFileRoute('/wishlist')({head:()=>pageHead('Your Wishlist','Keep your favorite ShopSphere finds in one place.'),component:Wishlist});
function Wishlist(){const{wishes}=useStore();return <section className="store-container py-12 min-h-96"><h1 className="text-3xl font-bold mb-8">Your favorites</h1>{wishes.length?<ProductGrid items={products.filter(p=>wishes.includes(p.id))}/>:<div className="text-center py-12"><Heart className="mx-auto text-primary size-10 mb-4"/><h2 className="font-semibold text-xl">A place for things you love.</h2><p className="text-muted-foreground my-4 text-sm">Save a favorite to come back to it later.</p><Button asChild><Link to="/shop" search={{}}>Discover your favorites</Link></Button></div>}</section>}
