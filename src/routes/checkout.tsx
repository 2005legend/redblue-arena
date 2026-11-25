import {createFileRoute,Link} from '@tanstack/react-router';
import {pageHead} from '@/lib/catalog';
import {Button} from '@/components/ui/button';
import {ShieldCheck} from 'lucide-react';
export const Route=createFileRoute('/checkout')({head:()=>pageHead('Checkout','Review your ShopSphere checkout and shipping details.'),component:()=> <section className="store-container py-14 min-h-96"><div className="max-w-lg mx-auto text-center"><ShieldCheck className="mx-auto size-12 text-primary mb-5"/><h1 className="text-3xl font-bold">Checkout is not connected yet.</h1><p className="text-muted-foreground text-sm leading-7 mt-5">Orders and simulated payments will be available when the isolated local store is connected. Your bag is ready; no payment information is collected.</p><Button asChild className="mt-6"><Link to="/cart">Back to your bag</Link></Button></div></section>});
