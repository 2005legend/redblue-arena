import {createFileRoute} from '@tanstack/react-router';
import {CatalogPage} from '@/components/catalog-page';
import {pageHead} from '@/lib/catalog';
export const Route=createFileRoute('/category/$category')({head:({params})=>pageHead(params.category,`Explore thoughtfully selected ${params.category.toLowerCase()} at ShopSphere.`),component:Category});
function Category(){const {category}=Route.useParams();return <CatalogPage key={category} initialCategory={category}/>}
