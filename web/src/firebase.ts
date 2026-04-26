import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyD-vzOiybXC-XvHqm4rg60Mpz0w8WtdCYs",
  authDomain: "unmute-1065b.firebaseapp.com",
  projectId: "unmute-1065b",
  storageBucket: "unmute-1065b.firebasestorage.app",
  messagingSenderId: "1079327945407",
  appId: "1:1079327945407:web:bc1791d1b58f82f5850c0a",
  measurementId: "G-KZNX63VDXW"
};

const app = initializeApp(firebaseConfig)
export const db = getFirestore(app)
export const auth = getAuth(app) 

