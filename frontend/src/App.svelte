<!-- meshop/frontend/src/App.svelte -->
<script>
	import { Router, Link, Route } from "svelte-routing";
	// import Home from "./routes/Home.svelte";
	import ProductList from "./routes/ProductList.svelte";
	import ProductDetail from "./routes/ProductDetail.svelte";
	// import Cart from "./routes/Cart.svelte";
	import Header from "./components/Header.svelte";
	import Footer from "./components/Footer.svelte";
  
	export let url = "";

	export const backend = "http://localhost:8000";
  </script>
  
  <Router {url}>
	<div class="app">
	  <Header />
	  <main>
		<!-- <Route path="/" component={Home} /> -->
		<Route path="/" component={ProductList} />
		<Route path="/product/:id" component={ProductDetail} />
	  </main>
	  <Footer />
	</div>
  </Router>
  
  <style>
	.app {
	  display: flex;
	  flex-direction: column;
	  min-height: 100vh;
	}
  
	main {
	  flex: 1;
	  padding: 1rem;
	}
  </style>