import {createFileRoute} from '@tanstack/react-router';
import {CatalogPage} from '@/components/catalog-page';
import {pageHead} from '@/lib/catalog';
export const Route=createFileRoute('/offers')({head:()=>pageHead('Deals & Offers','Discover savings on your favorite ShopSphere products.'),component:()=> <CatalogPage offers/>});
