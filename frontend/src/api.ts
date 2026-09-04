export type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function parseError(response: Response) {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data.detail)) {
      const error = data.detail[0];
      const field = error?.loc?.[error.loc.length - 1];

      switch (field) {
        case "name":
          return "O nome completo deve ter entre 3 e 100 caracteres.";

        case "email":
          return "Informe um endereço de e-mail válido.";

        case "password":
        case "password_confirmation":
          return "A senha deve conter no mínimo 8 caracteres, letras maiúsculas, minúsculas e números.";

        default:
          return "Verifique os dados informados e tente novamente.";
      }
    }

    return "Não foi possível concluir a operação.";
  } catch {
    return "Não foi possível concluir a operação.";
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}


export async function register(
  name: string,
  email: string,
  password: string,
  passwordConfirmation: string
): Promise<User> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
      email,
      password,
      password_confirmation: passwordConfirmation,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}


export async function getMe(token: string): Promise<User> {
  const response = await fetch(`${API_URL}/auth/me`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}

export async function logout(token: string): Promise<void> {
  await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}


export async function forgotPassword(
  email: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/forgot-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}


export async function resetPassword(
  token: string,
  password: string,
  passwordConfirmation: string
): Promise<{ message: string }> {
  const response = await fetch(`${API_URL}/auth/reset-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      token,
      password,
      password_confirmation: passwordConfirmation,
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}


export type DocumentResponse = {
  id: number;
  original_filename: string;
  size_bytes: number;
  status: string;
  uploaded_at: string;
  extracted_text: string | null;
  page_count: number | null;
  pages_without_text: number[];
};

export async function uploadDocument(
  token: string,
  file: File
): Promise<DocumentResponse> {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_URL}/documents/upload`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    throw new Error(
      await parseError(response)
    );
  }

  return response.json();
}
