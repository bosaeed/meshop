import { writable } from 'svelte/store';

// Create a writable store for the cart
export const cart = writable([]);

window.env = {
    "BACKEND_URL" :"https://meshop.onrender.com",//"https://meshop.onrender.com" "http://localhost:8000"
    "BACKEND_URL_WS": "wss://meshop.onrender.com/ws",//"wss://meshop.onrender.com/ws" "ws://localhost:8000/ws"
}

export const env = {  ...window['env'] }