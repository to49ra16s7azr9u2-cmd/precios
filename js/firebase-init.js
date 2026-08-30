// ComparaMX — puente de Firebase Authentication.
//
// Este archivo se carga como <script type="module">, así que puede usar
// import de ES modules, pero el resto del sitio (js/app.js) es un script
// clásico sin bundler. Por eso este módulo no habla directamente con
// app.js: expone todo en window.ComparaMXAuth y avisa que ya está listo
// disparando el evento "comparamx-auth-ready" -- app.js espera ese evento
// (o revisa si window.ComparaMXAuth ya existe, por si el módulo cargó
// primero) en vez de asumir un orden de ejecución entre script type=module
// (diferido) y script clásico.
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js";
import {
  getAuth,
  onAuthStateChanged,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signOut,
  updateProfile,
} from "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js";

const firebaseConfig = {
  apiKey: "AIzaSyABXhT-z1-61Ghb_H32X5o2pOdedFX0_zU",
  authDomain: "comparamx.firebaseapp.com",
  projectId: "comparamx",
  storageBucket: "comparamx.firebasestorage.app",
  messagingSenderId: "824084837594",
  appId: "1:824084837594:web:3f93b602032dbb7aa0a1e3",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

let currentUser = null;
const listeners = [];

function toPublicUser(u) {
  if (!u) return null;
  return { uid: u.uid, displayName: u.displayName, email: u.email, photoURL: u.photoURL };
}

onAuthStateChanged(auth, (u) => {
  currentUser = toPublicUser(u);
  listeners.forEach((cb) => {
    try {
      cb(currentUser);
    } catch {
      // un listener roto no debe tumbar a los demás
    }
  });
});

// Traduce los códigos de error de Firebase Auth (en inglés, tipo
// "auth/wrong-password") a un mensaje corto en español para mostrar en el
// formulario -- el usuario final no debería ver códigos técnicos.
function mapAuthError(code) {
  const map = {
    "auth/invalid-email": "El correo no es válido.",
    "auth/user-disabled": "Esta cuenta está deshabilitada.",
    "auth/user-not-found": "No encontramos una cuenta con ese correo.",
    "auth/wrong-password": "Contraseña incorrecta.",
    "auth/invalid-credential": "Correo o contraseña incorrectos.",
    "auth/email-already-in-use": "Ya existe una cuenta con ese correo.",
    "auth/weak-password": "La contraseña debe tener al menos 6 caracteres.",
    "auth/missing-password": "Escribe una contraseña.",
    "auth/popup-closed-by-user": "Cerraste la ventana antes de terminar el inicio de sesión.",
    "auth/cancelled-popup-request": "Cerraste la ventana antes de terminar el inicio de sesión.",
    "auth/popup-blocked": "Tu navegador bloqueó la ventana emergente. Permite ventanas emergentes para este sitio e intenta de nuevo.",
    "auth/network-request-failed": "Problema de conexión. Revisa tu internet e intenta de nuevo.",
    "auth/too-many-requests": "Demasiados intentos. Espera un momento e intenta de nuevo.",
  };
  return map[code] || "Ocurrió un error. Intenta de nuevo.";
}

async function guarded(fn) {
  try {
    await fn();
    return { ok: true };
  } catch (err) {
    return { ok: false, message: mapAuthError(err && err.code) };
  }
}

window.ComparaMXAuth = {
  getCurrentUser() {
    return currentUser;
  },
  onChange(callback) {
    listeners.push(callback);
    // Si ya se resolvió el estado inicial antes de suscribirse, avisa de
    // una vez con el valor actual (evita que quien se suscribe tarde se
    // quede esperando el próximo cambio, que puede no llegar nunca).
    if (auth.currentUser !== undefined) callback(currentUser);
  },
  signInGoogle() {
    return guarded(() => signInWithPopup(auth, googleProvider));
  },
  signInEmail(email, password) {
    return guarded(() => signInWithEmailAndPassword(auth, email, password));
  },
  signUpEmail(email, password) {
    return guarded(() => createUserWithEmailAndPassword(auth, email, password));
  },
  resetPassword(email) {
    return guarded(() => sendPasswordResetEmail(auth, email));
  },
  signOutUser() {
    return guarded(() => signOut(auth));
  },
  updateDisplayName(name) {
    return guarded(async () => {
      if (!auth.currentUser) throw new Error("not-signed-in");
      await updateProfile(auth.currentUser, { displayName: name });
      currentUser = toPublicUser(auth.currentUser);
      listeners.forEach((cb) => {
        try {
          cb(currentUser);
        } catch {
          // ver arriba
        }
      });
    });
  },
};

window.dispatchEvent(new CustomEvent("comparamx-auth-ready"));
