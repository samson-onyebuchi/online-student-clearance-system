/* =========================================================
   STUDENT CLEARANCE PORTAL
   LOGIN PAGE JAVASCRIPT
   File: js/index.js

   FUNCTIONS:
   1. Connect to the local Flask backend.
   2. Log in students using registration number and password.
   3. Display login success and error messages.
   4. Show or hide the password.
   5. Redirect students to the dashboard after successful login.
   6. Display the current year in the footer.
   7. Add subtle login interface interactions and feedback.
   8. Support decorative elements without requiring them.

   IMPORTANT:
   - No token authentication is used.
   - HTML files are directly inside Frontend.
   - CSS files are inside Frontend/css.
   - JavaScript files are inside Frontend/js.
========================================================= */


/* =========================================================
   1. CONFIGURATION
========================================================= */

// Local Flask backend URL.
const API_BASE_URL = "http://127.0.0.1:5000";

// Student login endpoint.
const STUDENT_LOGIN_URL =
    `${API_BASE_URL}/api/v1/clearance/login/student`;

// Dashboard HTML is directly inside Frontend.
// This JavaScript file is inside Frontend/js.
// The redirect is resolved relative to the current HTML page.
const STUDENT_DASHBOARD_URL = "./student-dashboard.html";


/* =========================================================
   2. GET HTML ELEMENTS
========================================================= */

const loginForm = document.getElementById("loginForm");
const regNoInput = document.getElementById("reg_no");
const passwordInput = document.getElementById("password");

const loginButton = document.getElementById("loginButton");
const loginMessage = document.getElementById("loginMessage");

const currentYearElement = document.getElementById("currentYear");


/* =========================================================
   3. DISPLAY LOGIN MESSAGES
========================================================= */

function showLoginMessage(message, type = "error") {
    if (!loginMessage) {
        console[type === "error" ? "error" : "log"](message);
        return;
    }

    loginMessage.textContent = message;
    loginMessage.className = `form-message ${type}`;
    loginMessage.setAttribute("role", "status");
    loginMessage.setAttribute("aria-live", "polite");
    loginMessage.style.display = "block";
}

function clearLoginMessage() {
    if (!loginMessage) {
        return;
    }

    loginMessage.textContent = "";
    loginMessage.className = "form-message";
    loginMessage.style.display = "none";
}


/* =========================================================
   4. LOGIN BUTTON LOADING STATE
========================================================= */

// Remember the original button text so we can restore it.
const originalLoginButtonText = loginButton
    ? loginButton.textContent.trim() || "Sign In"
    : "Sign In";

function setLoginLoading(isLoading) {
    if (!loginButton) {
        return;
    }

    loginButton.disabled = isLoading;
    loginButton.setAttribute("aria-busy", String(isLoading));

    if (isLoading) {
        loginButton.textContent = "Signing In...";
        loginButton.classList.add("is-loading");
    } else {
        loginButton.textContent = originalLoginButtonText;
        loginButton.classList.remove("is-loading");
    }
}


/* =========================================================
   5. SEND LOGIN REQUEST TO FLASK
========================================================= */

async function loginStudent(regNo, password) {
    const response = await fetch(STUDENT_LOGIN_URL, {
        method: "POST",

        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },

        body: JSON.stringify({
            reg_no: regNo,
            password: password
        })
    });

    // Handle invalid JSON responses safely.
    let result;

    try {
        result = await response.json();
    } catch {
        throw new Error(
            "The server returned an invalid response. Please try again."
        );
    }

    // Handle HTTP errors and unsuccessful authentication.
    if (!response.ok || result.status !== "success") {
        throw new Error(
            result.message ||
            "Login failed. Check your registration number and password."
        );
    }

    // Ensure the backend returned student information.
    if (!result.data) {
        throw new Error(
            "Login response did not contain student information."
        );
    }

    return result.data;
}


/* =========================================================
   6. HANDLE STUDENT LOGIN FORM
========================================================= */

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        clearLoginMessage();

        // Confirm the required form elements exist.
        if (!regNoInput || !passwordInput) {
            showLoginMessage(
                "The login form is missing a required input. Please check index.html."
            );
            return;
        }

        // Read student login details.
        const regNo = regNoInput.value.trim().toUpperCase();
        const password = passwordInput.value;

        // Validate registration number.
        if (!regNo) {
            showLoginMessage(
                "Please enter your registration number."
            );

            regNoInput.focus();
            return;
        }

        // Validate password.
        if (!password) {
            showLoginMessage(
                "Please enter your password."
            );

            passwordInput.focus();
            return;
        }

        setLoginLoading(true);

        try {
            // Authenticate the student with Flask.
            const student = await loginStudent(regNo, password);

            // Save student information for the dashboard.
            // No authentication token is stored.
            try {
                sessionStorage.setItem(
                    "clearanceStudent",
                    JSON.stringify(student)
                );

                sessionStorage.setItem(
                    "studentRegNo",
                    student.reg_no || regNo
                );
            } catch (storageError) {
                console.error(
                    "Unable to save student session:",
                    storageError
                );

                showLoginMessage(
                    "Your browser could not save the login session. " +
                    "Enable session storage and try again."
                );

                setLoginLoading(false);
                return;
            }

            // Display successful login feedback.
            showLoginMessage(
                "Login successful. Opening your dashboard...",
                "success"
            );

            // Navigate to the dashboard HTML in Frontend.
            window.location.assign(STUDENT_DASHBOARD_URL);

        } catch (error) {
            console.error("Student login error:", error);

            let message = error.message ||
                "An unexpected error occurred. Please try again.";

            // Provide a useful message for backend connection failures.
            if (
                error instanceof TypeError &&
                /fetch|network/i.test(error.message)
            ) {
                message =
                    "Unable to connect to the backend. Make sure Flask is " +
                    "running at http://127.0.0.1:5000 and check your CORS settings.";
            }

            showLoginMessage(message, "error");

            setLoginLoading(false);
        }
    });
} else {
    console.warn(
        "Login form not found. Confirm that index.html contains id=\"loginForm\"."
    );
}


/* =========================================================
   7. SHOW OR HIDE PASSWORD
========================================================= */

document.querySelectorAll("[data-toggle-password]").forEach(
    function (toggleButton) {
        toggleButton.addEventListener("click", function () {
            const inputId = toggleButton.getAttribute(
                "data-toggle-password"
            );

            const passwordField = document.getElementById(inputId);

            if (!passwordField) {
                console.warn(
                    `Password input with ID "${inputId}" was not found.`
                );
                return;
            }

            const isPasswordHidden =
                passwordField.type === "password";

            passwordField.type = isPasswordHidden
                ? "text"
                : "password";

            toggleButton.textContent = isPasswordHidden
                ? "Hide"
                : "Show";

            toggleButton.setAttribute(
                "aria-label",
                isPasswordHidden
                    ? "Hide password"
                    : "Show password"
            );

            toggleButton.setAttribute(
                "aria-pressed",
                String(isPasswordHidden)
            );
        });
    }
);


/* =========================================================
   8. DISPLAY CURRENT YEAR
========================================================= */

if (currentYearElement) {
    currentYearElement.textContent = new Date().getFullYear();
}


/* =========================================================
   9. CLEAR ERROR MESSAGE WHEN USER EDITS LOGIN DETAILS
========================================================= */

if (regNoInput) {
    regNoInput.addEventListener("input", clearLoginMessage);
}

if (passwordInput) {
    passwordInput.addEventListener("input", clearLoginMessage);
}


/* =========================================================
   10. OPTIONAL DECORATIVE INTERACTIONS
========================================================= */

// Add a class when the user interacts with the login form.
// This can be used by CSS for subtle visual feedback.
if (loginForm) {
    loginForm.addEventListener("focusin", function () {
        loginForm.classList.add("form-active");
    });

    loginForm.addEventListener("focusout", function (event) {
        if (!loginForm.contains(event.relatedTarget)) {
            loginForm.classList.remove("form-active");
        }
    });
}

// Optional current-page indicator for elements that support it.
document.querySelectorAll("[data-current-page]").forEach(
    function (element) {
        element.setAttribute("aria-current", "page");
    }
);