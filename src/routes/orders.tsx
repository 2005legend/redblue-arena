import {createFileRoute,Link} from '@tanstack/react-router';
import {Package} from 'lucide-react';
import {pageHead} from '@/lib/catalog';
import {Button} from '@/components/ui/button';
export const Route=createFileRoute('/orders')({head:()=>pageHead('Your Orders','View and track your ShopSphere orders.'),component:()=> <section className="store-container py-12 min-h-96"><h1 className="text-3xl font-bold">Your orders</h1><div className="text-center py-14"><Package className="mx-auto size-10 text-primary mb-5"/><h2 className="text-xl font-semibold">Your finds, all in one place.</h2><p className="text-muted-foreground text-sm mt-3 mb-6">Sign in to see your order history and delivery details.</p><Button asChild><Link to="/account">Sign In</Link></Button></div></section>});
