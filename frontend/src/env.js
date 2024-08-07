import { writable } from 'svelte/store';

// Create a writable store for the cart
export const cart = writable([]);

window.env = {
    "BACKEND_URL" :"https://meshop.bosaeed.top",//"https://meshop.onrender.com" "http://localhost:8000" "https://meshop.bosaeed.top"
    "BACKEND_URL_WS": "wss://meshop.bosaeed.top/ws",//"wss://meshop.onrender.com/ws" "ws://localhost:8000/ws" "wss://meshop.bosaeed.top/ws"
}

export const env = {  ...window['env'] }