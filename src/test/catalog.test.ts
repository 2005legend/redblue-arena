import {describe,it,expect} from 'vitest';
import {products,categories,filterProducts} from '@/lib/catalog';
describe('ShopSphere catalog',()=>{
 it('contains at least 30 individually addressable products',()=>{expect(products.length).toBeGreaterThanOrEqual(30);expect(new Set(products.map(p=>p.id)).size).toBe(products.length);});
 it('includes all six requested categories',()=>{expect(categories).toEqual(['Electronics','Fashion','Home & Living','Accessories','Books','Sports & Fitness']);for(const category of categories)expect(products.some(p=>p.category===category)).toBe(true);});
 it('searches real catalog entries case insensitively',()=>{const found=filterProducts('BOTTLE','',250,'featured');expect(found).toHaveLength(4);expect(found.every(p=>p.name.toLowerCase().includes('bottle'))).toBe(true);expect(filterProducts('nonexistent','',250,'featured')).toHaveLength(0);});
 it('combines category and price filtering',()=>{const found=filterProducts('','Electronics',90,'featured');expect(found.length).toBeGreaterThan(0);expect(found.every(p=>p.category==='Electronics'&&p.price<=90)).toBe(true);expect(found.some(p=>p.id==='1')).toBe(false);});
 it('sorts by price without modifying the source catalog',()=>{const found=filterProducts('','',250,'price-low');expect(found[0]?.price).toBe(24.99);expect(products[0]?.id).toBe('1');});
 it('prioritizes new arrivals',()=>{expect(filterProducts('','',250,'new')[0]?.badge).toBe('NEW');});
});