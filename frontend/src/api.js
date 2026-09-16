const BASE_URL = "http://127.0.0.1:8001";

function getHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

export async function login(username, password) {
    const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error('Login failed');
    return await res.json();
}

export async function fetchWithAuth(endpoint, options = {}) {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: getHeaders()
    });
    if (res.status === 401 || res.status === 403) {
        throw new Error(res.status === 401 ? "Unauthorized" : "Forbidden");
    }
    return res;
}
