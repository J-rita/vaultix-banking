const API_BASE = "/api/auth";

// Registration Logic
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            first_name: document.getElementById('firstName').value,
            last_name: document.getElementById('lastName').value,
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value
        };

        try {
            const response = await fetch(`${API_BASE}/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                const text = await response.text();
                console.error("Non-JSON response:", text);
                throw new Error("Server error: Received non-JSON response from server.");
            }

            const result = await response.json();
            
            if (result.status === "success") {
                alert("Vaultix Account created successfully! Please login.");
                window.location.href = 'login.html';
            } else {
                alert("Vaultix Error: " + (result.detail || "Registration failed"));
            }
        } catch (error) {
            console.error("Detailed Error:", error);
            alert("Connection error: " + error.message);
        }
    });
}

// Login Logic
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        };

        try {
            const response = await fetch(`${API_BASE}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.status === "success") {
                localStorage.setItem('token', result.access_token);
                localStorage.setItem('role', result.role);
                localStorage.setItem('username', data.username);
                
                if (result.role === 'Admin') {
                    window.location.href = 'admin.html';
                } else {
                    window.location.href = 'dashboard.html';
                }
            } else {
                alert("Login Error: " + (result.detail || "Invalid credentials"));
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Connection error: " + error.message);
        }
    });
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}
