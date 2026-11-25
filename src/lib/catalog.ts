import headphones from '@/assets/headphones.webp.asset.json';
import sneakers from '@/assets/sneakers.webp.asset.json';
import lamp from '@/assets/lamp.webp.asset.json';
import watch from '@/assets/watch.webp.asset.json';
import backpack from '@/assets/backpack.webp.asset.json';
import books from '@/assets/books.webp.asset.json';
import bottle from '@/assets/bottle.webp.asset.json';
import earbuds from '@/assets/earbuds.webp.asset.json';
export const categories = ['Electronics', 'Fashion', 'Home & Living', 'Accessories', 'Books', 'Sports & Fitness'];
export type Product = { id: string; name: string; category: string; price: number; original: number; image: string; rating: number; reviews: number; stock: number; badge: string; description: string };
const base = [
 ['Studio Wireless Headphones','Electronics',129.99,179.99,headphones.url,'BESTSELLER'],
 ['Everyday Classic Sneakers','Fashion',69.99,89.99,sneakers.url,'SALE'],
 ['Aura Mushroom Table Lamp','Home & Living',49.99,65.99,lamp.url,'NEW'],
 ['Pulse Smart Watch','Electronics',89.99,119.99,watch.url,'SALE'],
 ['The Everyday Canvas Backpack','Accessories',54.99,74.99,backpack.url,''],
 ['The Art of Slow Living Collection','Books',34.99,44.99,books.url,''],
 ['Hydra Insulated Water Bottle','Sports & Fitness',24.99,32.99,bottle.url,''],
 ['Airwave Wireless Earbuds','Electronics',59.99,79.99,earbuds.url,'NEW'],
] as const;
export const products: Product[] = Array.from({length:32}, (_,i) => {
 const b=base[i%8]; if(!b) throw new Error('Missing catalog item');
 const edition=['',' · Essential Edition',' · Signature Edition',' · Premium Edition'][Math.floor(i/8)] ?? '';
 return {id:String(i+1),name:b[0]+edition,category:b[1],price:Number((b[2]+Math.floor(i/8)*10).toFixed(2)),original:b[3]+Math.floor(i/8)*12,image:b[4],rating:4.8-(i%3)*0.1,reviews:124+i*17,stock:25+i,badge:b[5],description:`Meet your new everyday favorite. The ${b[0].toLowerCase()} combines thoughtful design, lasting quality, and effortless everyday comfort. Carefully selected for the way you live.`};
});
export const money=(n:number)=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD'}).format(n);
export function filterProducts(query:string,category:string,maxPrice:number,sort:string){
 const list=products.filter(p=>p.name.toLowerCase().includes(query.toLowerCase())&&(!category||p.category===category)&&p.price<=maxPrice);
 if(sort==='price-low')list.sort((a,b)=>a.price-b.price);
 if(sort==='price-high')list.sort((a,b)=>b.price-a.price);
 if(sort==='rating')list.sort((a,b)=>b.rating-a.rating);
 if(sort==='new')list.sort((a,b)=>Number(b.badge==='NEW')-Number(a.badge==='NEW')||Number(b.id)-Number(a.id));
 return list;
}
export function pageHead(title:string,description:string){return {meta:[{title:`${title} | ShopSphere`},{name:'description',content:description},{property:'og:title',content:`${title} | ShopSphere`},{property:'og:description',content:description},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]};}
