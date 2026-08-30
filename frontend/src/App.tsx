import { useEffect, useState } from "react";
import { Scale } from "lucide-react";

import { getMe, type User } from "./api";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Register from "./pages/Register";

const TOKEN_KEY = "sapia_token";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authPage, setAuthPage] = useState<"login" | "register">("login");

  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
  );

  const [booting, setBooting] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setBooting(false);
      return;
    }

    getMe(token)
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setBooting(false));
  }, [token]);

  if (booting) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">
          <Scale size={28} />
        </div>

        <span>Carregando SAPIA...</span>
      </div>
    );
  }

  if (!user || !token) {
    if (authPage === "register") {
      return (
        <Register
          onBackToLogin={() => setAuthPage("login")}
        />
      );
    }

    return (
      <Login
        onAuthenticated={(user, token) => {
          localStorage.setItem(TOKEN_KEY, token);
          setToken(token);
          setUser(user);
        }}
        onRegister={() => setAuthPage("register")}
      />
    );
}

  return (
    <Home
      user={user}
      token={token}
      onLogout={() => {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setToken(null);
      }}
    />
  );
}