<!-- meshop/frontend/src/routes/Home.svelte -->
<script>
    import { Link } from "svelte-routing";
  </script>
  
  <h1>Welcome to MeShop</h1>
  <p>Discover our amazing products!</p>
  <Link to="/products">
    <button>Shop Now</button>
  </Link>