/* =========================================================
   STUDENT CLEARANCE PORTAL
   STUDENT DASHBOARD JAVASCRIPT
   File: js/student-Interface.js

   FEATURES:
   1. Restore logged-in student session and local cache.
   2. Display student profile information.
   3. Navigate seamlessly between dashboard sections.
   4. Create and view final-year clearance with persistence.
   5. Display all eight clearance stages and progress.
   6. Upload PDF, DOC, and DOCX files.
   7. List, view, and download uploaded documents.
   8. Change account password securely.
   9. Display activity feed and notifications.
   10. Support mobile sidebar toggles.
   11. Local environment compatibility.
========================================================= */

"use strict";

/* =========================================================
   1. API CONFIGURATION
========================================================= */

const API_BASE_URL = "http://127.0.0.1:5000";

const API = {
    clearanceCreate:
        `${API_BASE_URL}/api/v1/clearance/create`,

    clearanceView:
        `${API_BASE_URL}/api/v1/clearance/view`,

    documents:
        `${API_BASE_URL}/api/v1/clearance/documents`,

    uploadDocument:
        `${API_BASE_URL}/api/v1/clearance/upload-document`,

    viewDocument:
        `${API_BASE_URL}/api/v1/clearance/document/view`,

    downloadDocument:
        `${API_BASE_URL}/api/v1/clearance/document/download`,

    changePassword:
        `${API_BASE_URL}/api/v1/clearance/reset-password/student`
};

/* =========================================================
   2. CLEARANCE STAGES
========================================================= */

const STAGES = [
    { key: "department", label: "Department" },
    { key: "finance", label: "Finance" },
    { key: "library", label: "Library" },
    { key: "alumni", label: "Alumni" },
    { key: "student_affairs", label: "Student Affairs" },
    { key: "health", label: "Health" },
    { key: "security", label: "Security" },
    { key: "audit", label: "Audit" }
];

const ALLOWED_FILE_EXTENSIONS = ["pdf", "doc", "docx"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

/* =========================================================
   3. DASHBOARD STATE
========================================================= */

let student = null;
let clearance = null;
let uploadedDocuments = [];
let currentViewedStage = null;
let selectedFile = null;
let uploadInProgress = false;

/* =========================================================
   4. GENERAL HELPERS
========================================================= */

function getElement(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = getElement(id);

    if (element) {
        element.textContent =
            value === undefined || value === null || value === ""
                ? "Not available"
                : String(value);
    }
}

function safeString(value) {
    return value === undefined || value === null
        ? ""
        : String(value);
}

function escapeHTML(value) {
    return safeString(value).replace(/[&<>"']/g, character => {
        const replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return replacements[character];
    });
}

function normalizeStatus(status) {
    return safeString(status)
        .trim()
        .toLowerCase()
        .replace(/[\s-]+/g, "_");
}

function humanizeStatus(status) {
    const value = safeString(status);

    if (!value) {
        return "Not Started";
    }

    return value
        .replace(/_/g, " ")
        .replace(/\b\w/g, character => character.toUpperCase());
}

function getStudentRegNo() {
    if (student) {
        const val = student.reg_no || student.registration_number || student.regNo;
        if (val) return String(val).trim();
    }

    const storedReg = sessionStorage.getItem("studentRegNo") || sessionStorage.getItem("reg_no");
    if (storedReg) return storedReg.trim();

    const storedStudentJson = sessionStorage.getItem("clearanceStudent");
    if (storedStudentJson) {
        try {
            const parsed = JSON.parse(storedStudentJson);
            const val = parsed.reg_no || parsed.registration_number || parsed.regNo || parsed.data?.reg_no;
            if (val) return String(val).trim();
        } catch (e) {
            // silent catch
        }
    }

    return "";
}

function getStudentFullName() {
    if (!student) {
        return "Student";
    }

    const names = [
        student.surname,
        student.first_name,
        student.other_names
    ].filter(value => safeString(value).trim());

    return names.join(" ") || "Student";
}

function getStageLabel(stageKey) {
    const stage = STAGES.find(item => item.key === stageKey);

    return stage ? stage.label : humanizeStatus(stageKey);
}

function getStageIndex(stageKey) {
    return STAGES.findIndex(stage => stage.key === stageKey);
}

function formatDate(value) {
    if (!value) {
        return "Not available";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return safeString(value);
    }

    return date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric"
    });
}

function showMessage(elementId, message, type = "info") {
    const element = getElement(elementId);

    if (element) {
        element.textContent = message;
        element.className = `form-message ${type}`;
        element.hidden = !message;
    }

    if (message && type === "error") {
        showToast(message, "error");
    }
}

function showToast(message, type = "info") {
    const container = getElement("toastContainer");

    if (!container) {
        console.log(message);
        return;
    }

    const toast = document.createElement("div");
    toast.className = `toast-message toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    window.setTimeout(() => {
        toast.remove();
    }, 5000);
}

function setButtonLoading(button, loading, loadingText = "Please wait...") {
    if (!button) {
        return;
    }

    if (loading) {
        if (!button.dataset.originalText) {
            button.dataset.originalText = button.innerHTML;
        }

        button.disabled = true;
        button.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${escapeHTML(loadingText)}`;
    } else {
        button.disabled = false;

        if (button.dataset.originalText) {
            button.innerHTML = button.dataset.originalText;
            delete button.dataset.originalText;
        }
    }
}

/* =========================================================
   5. BACKEND REQUEST HELPER
========================================================= */

async function requestJSON(url, options = {}) {
    const response = await fetch(url, options);

    let result = {};

    try {
        result = await response.json();
    } catch (error) {
        result = {};
    }

    if (!response.ok) {
        const message =
            result.message ||
            result.error ||
            result.description ||
            `Request failed with HTTP ${response.status}.`;

        const requestError = new Error(message);

        requestError.status = response.status;
        requestError.responseData = result;

        throw requestError;
    }

    if (
        result.status &&
        ["error", "failed", "failure"].includes(
            safeString(result.status).toLowerCase()
        )
    ) {
        const requestError = new Error(
            result.message ||
            result.error ||
            "The request was unsuccessful."
        );

        requestError.status = response.status;
        requestError.responseData = result;

        throw requestError;
    }

    return result;
}

function getResponseData(result) {
    if (!result || typeof result !== "object") {
        return result;
    }

    if (result.data !== undefined && result.data !== null) {
        return result.data;
    }

    return result;
}

function extractClearanceRecord(result) {
    if (!result || typeof result !== "object") {
        return null;
    }

    const candidates = [
        result,
        result.data,
        result.clearance,
        result.data?.clearance,
        result.data?.data,
        result.data?.data?.clearance,
        result.result,
        result.result?.clearance
    ];

    for (const candidate of candidates) {
        if (
            candidate &&
            typeof candidate === "object" &&
            !Array.isArray(candidate)
        ) {
            const hasClearanceFields = [
                "clearance_id",
                "clearanceId",
                "current_stage",
                "currentStage",
                "stage_status",
                "stages",
                "reg_no"
            ].some(key => candidate[key] !== undefined);

            if (hasClearanceFields) {
                return candidate;
            }
        }
    }

    return null;
}

function isClearanceNotFoundError(error) {
    if (!error || error.status !== 404) {
        return false;
    }

    const message = safeString(error.message).toLowerCase();

    return [
        /has not started the clearance process/,
        /clearance.*not found/,
        /no clearance record/,
        /clearance record.*does not exist/
    ].some(pattern => pattern.test(message));
}

/* =========================================================
   6. SESSION RESTORATION
========================================================= */

function restoreStudentSession() {
    const storedStudent = sessionStorage.getItem("clearanceStudent");

    if (storedStudent) {
        try {
            student = JSON.parse(storedStudent);
        } catch (error) {
            student = null;
        }
    }

    if (!student || !getStudentRegNo()) {
        const regNo = sessionStorage.getItem("studentRegNo");

        if (regNo) {
            student = { ...(student || {}), reg_no: regNo };
        }
    }

    if (!student || !getStudentRegNo()) {
        window.location.replace("./index.html");
        return false;
    }

    const cachedClearance = sessionStorage.getItem("clearanceRecord");

    if (cachedClearance) {
        try {
            clearance = JSON.parse(cachedClearance);
        } catch (e) {
            clearance = null;
        }
    }

    return true;
}

/* =========================================================
   7. STUDENT PROFILE
========================================================= */

function renderStudentProfile() {
    if (!student) {
        return;
    }

    const fullName = getStudentFullName();
    const regNo = getStudentRegNo();

    setText("welcomeStudentName", fullName);
    setText("headerStudentName", fullName);
    setText("sidebarRegNo", regNo);

    setText("profileFullName", fullName);
    setText("profileRegistrationNumber", regNo);
    setText("profileEmail", student.email);
    setText("profilePhone", student.phone_number);
    setText("profileDepartment", student.department);
    setText("profileFaculty", student.faculty);
    setText("profileGender", student.gender);
    setText("profileStudentCategory", student.student_status || student.student_category);

    document.title = `${fullName} | Student Clearance Portal`;
}

/* =========================================================
   8. DASHBOARD NAVIGATION
========================================================= */

const SECTION_DETAILS = {
    overview: { title: "Dashboard Overview", subtitle: "Manage your final-year clearance progress." },
    clearance: { title: "My Clearance", subtitle: "Track your final-year institutional checkpoints." },
    documents: { title: "My Documents", subtitle: "Upload and review clearance document submissions." },
    profileDetailsPage: { title: "My Profile", subtitle: "Review your personal and academic student records." },
    notifications: { title: "Notifications", subtitle: "Check official updates and officer feedbacks." },
    changePassword: { title: "Change Password", subtitle: "Secure your account credentials." }
};

function showSection(sectionId) {
    const target = getElement(sectionId);

    if (!target || !target.hasAttribute("data-dashboard-section")) {
        return;
    }

    document.querySelectorAll("[data-dashboard-section]").forEach(section => {
        const active = section.id === sectionId;
        section.hidden = !active;
        section.classList.toggle("active", active);
    });

    document.querySelectorAll("[data-section-target]").forEach(link => {
        link.classList.toggle("active", link.dataset.sectionTarget === sectionId);
    });

    const details = SECTION_DETAILS[sectionId];

    if (details) {
        setText("pageTitle", details.title);
        setText("pageSubtitle", details.subtitle);
    }

    closeSidebar();

    if (sectionId === "documents") {
        updateUploadAvailability();
        renderDocuments();
    }

    if (sectionId === "notifications") {
        renderNotifications();
    }

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupNavigation() {
    document.querySelectorAll("[data-section-target]").forEach(element => {
        element.addEventListener("click", event => {
            event.preventDefault();
            const sectionId = element.dataset.sectionTarget;
            if (sectionId) {
                showSection(sectionId);
            }
        });
    });

    document.querySelectorAll("[data-stage]").forEach(button => {
        button.addEventListener("click", () => {
            openStage(button.dataset.stage);
        });
    });
}

/* =========================================================
   9. SIDEBAR CONTROLS
========================================================= */

function openSidebar() {
    const sidebar = getElement("sidebar");
    const overlay = getElement("sidebarOverlay");

    if (sidebar) sidebar.classList.add("open", "active");
    if (overlay) overlay.classList.add("active");
}

function closeSidebar() {
    const sidebar = getElement("sidebar");
    const overlay = getElement("sidebarOverlay");

    if (sidebar) sidebar.classList.remove("open", "active");
    if (overlay) overlay.classList.remove("active");
}

function setupSidebar() {
    const toggles = [getElement("sidebarToggle"), getElement("menuToggle")].filter(Boolean);

    toggles.forEach(btn => {
        btn.addEventListener("click", () => {
            const sidebar = getElement("sidebar");
            if (sidebar && sidebar.classList.contains("open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    });

    const closeBtn = getElement("sidebarClose");
    if (closeBtn) closeBtn.addEventListener("click", closeSidebar);

    const overlay = getElement("sidebarOverlay");
    if (overlay) overlay.addEventListener("click", closeSidebar);

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeSidebar();
    });
}

/* =========================================================
   10. CLEARANCE DATA & STATUS
========================================================= */

function getClearanceStageStatuses() {
    if (!clearance) return {};
    return clearance.stages || clearance.stage_statuses || {};
}

function getStageStatus(stageKey) {
    if (!clearance || !stageKey) return "not_started";

    const stagesMap = getClearanceStageStatuses();
    const stageObj = stagesMap[stageKey];

    if (typeof stageObj === "string") {
        return normalizeStatus(stageObj);
    }

    if (stageObj && typeof stageObj === "object") {
        return normalizeStatus(stageObj.status || "pending");
    }

    const backendStage = normalizeStatus(clearance.current_stage);

    if (backendStage === normalizeStatus(stageKey)) {
        return normalizeStatus(clearance.stage_status || "pending");
    }

    return "not_started";
}

function isApproved(status) {
    return ["approved", "completed", "complete", "cleared", "verified"].includes(normalizeStatus(status));
}

function isRejected(status) {
    return normalizeStatus(status) === "rejected";
}

function isUnderReview(status) {
    return ["under_review", "pending_review", "submitted", "in_review"].includes(normalizeStatus(status));
}

function isClearanceCompleted() {
    if (!clearance) return false;
    if (["completed", "complete", "cleared"].includes(normalizeStatus(clearance.status))) return true;

    const stagesMap = getClearanceStageStatuses();
    if (Object.keys(stagesMap).length > 0 && STAGES.every(s => isApproved(getStageStatus(s.key)))) {
        return true;
    }

    return false;
}

function getCurrentStageKey() {
    if (!clearance || isClearanceCompleted()) return null;

    const backendStage = normalizeStatus(clearance.current_stage);
    if (STAGES.some(s => s.key === backendStage)) {
        return backendStage;
    }

    const firstIncomplete = STAGES.find(s => !isApproved(getStageStatus(s.key)));
    return firstIncomplete ? firstIncomplete.key : null;
}

function getProgressPercentage() {
    if (!clearance) return 0;
    if (isClearanceCompleted()) return 100;

    const approvedCount = STAGES.filter(s => isApproved(getStageStatus(s.key))).length;
    return Math.round((approvedCount / STAGES.length) * 100);
}

function getStageDescription(stageKey) {
    const status = getStageStatus(stageKey);

    if (isApproved(status)) return "This stage has been approved.";
    if (isRejected(status)) return "Your submission was rejected. Review feedback and re-upload.";
    if (isUnderReview(status)) return "Document submitted and awaiting officer review.";
    if (stageKey === getCurrentStageKey()) return "This is your active clearance stage.";

    return "This stage is locked until preceding stages are cleared.";
}

/* =========================================================
   11. FETCH CLEARANCE
========================================================= */

async function fetchClearance() {
    const regNo = getStudentRegNo();
    if (!regNo) {
        console.warn("fetchClearance skipped: Student registration number is empty.");
        return null;
    }

    const url = new URL(API.clearanceView);
    url.searchParams.set("reg_no", regNo);

    try {
        const result = await requestJSON(url.toString(), {
            method: "GET",
            headers: { "Accept": "application/json" },
            cache: "no-store"
        });

        const record = extractClearanceRecord(result);
        if (!record) {
            throw new Error("Invalid clearance record structure.");
        }

        if (!record.stages && clearance && clearance.stages) {
            record.stages = clearance.stages;
        } else if (!record.stages) {
            record.stages = {};
            STAGES.forEach(s => {
                record.stages[s.key] = {
                    status: s.key === record.current_stage ? (record.stage_status || "pending") : "pending",
                    documents: []
                };
            });
        }

        clearance = record;
        sessionStorage.setItem("clearanceRecord", JSON.stringify(clearance));

        renderClearance();
        return clearance;

    } catch (error) {
        if (isClearanceNotFoundError(error) || error.status === 404) {
            clearance = null;
            sessionStorage.removeItem("clearanceRecord");
            renderClearance();
            return null;
        }
        throw error;
    }
}

/* =========================================================
   12. RENDER CLEARANCE PROGRESS
========================================================= */

function renderClearance() {
    const completedCount = STAGES.filter(s => isApproved(getStageStatus(s.key))).length;
    const pendingCount = STAGES.filter(s => isUnderReview(getStageStatus(s.key))).length;
    const percentage = getProgressPercentage();
    const currentStage = getCurrentStageKey();
    const completed = isClearanceCompleted();

    const overallStatus = !clearance
        ? "Not Started"
        : completed
            ? "Completed"
            : humanizeStatus(clearance.status || "in_progress");

    setText("overallStatus", overallStatus);
    setText("currentStageName", completed ? "Completed" : currentStage ? getStageLabel(currentStage) : "Not Started");
    setText("approvedStages", completedCount);
    setText("pendingReviews", pendingCount);
    setText("completedStages", `${completedCount} stages completed`);
    setText("overallProgressPercentage", `${percentage}%`);

    const progressFill = getElement("overallProgressFill");
    if (progressFill) progressFill.style.width = `${percentage}%`;

    const progressPercentageBar = getElement("progressPercentage");
    if (progressPercentageBar) progressPercentageBar.style.width = `${percentage}%`;

    setText(
        "currentStageDescription",
        !clearance
            ? "Start your final-year clearance to initialize your workflow."
            : completed
                ? "Congratulations! All clearance stages have been successfully approved."
                : currentStage
                    ? getStageDescription(currentStage)
                    : "Clearance is active."
    );

    const badge = getElement("clearanceStatusBadge");
    if (badge) {
        badge.textContent = overallStatus;
        badge.className = `status-badge ${completed ? "status-approved" : clearance ? "status-pending" : "status-pending"}`;
    }

    updateStageCards();
    updateStageAction();
    updateUploadAvailability();
}

function updateStageCards() {
    document.querySelectorAll("[data-stage]").forEach(card => {
        const stageKey = card.dataset.stage;
        const status = getStageStatus(stageKey);
        const currentStage = getCurrentStageKey();

        card.classList.remove("stage-approved", "stage-pending", "stage-rejected", "stage-current", "stage-locked");

        if (isApproved(status)) card.classList.add("stage-approved");
        else if (isRejected(status)) card.classList.add("stage-rejected");
        else if (isUnderReview(status)) card.classList.add("stage-pending");

        if (stageKey === currentStage) card.classList.add("stage-current");

        const statusEl = card.querySelector("[data-stage-status]");
        if (statusEl) statusEl.textContent = humanizeStatus(status);
    });
}

function updateStageAction() {
    const startButton = getElement("startClearanceButton");
    const currentButton = getElement("currentStageActionButton");
    const actionTitle = getElement("stageActionTitle");
    const actionDescription = getElement("stageActionDescription");
    const completed = isClearanceCompleted();
    const currentStage = getCurrentStageKey();

    if (!clearance) {
        if (startButton) startButton.hidden = false;
        if (currentButton) currentButton.hidden = true;
        if (actionTitle) actionTitle.textContent = "Ready to begin?";
        if (actionDescription) actionDescription.textContent = "Start your final-year clearance to begin the approval process.";
        return;
    }

    if (startButton) startButton.hidden = true;

    if (completed) {
        if (currentButton) currentButton.hidden = true;
        if (actionTitle) actionTitle.textContent = "Clearance Completed";
        if (actionDescription) actionDescription.textContent = "All institutional checkpoints have been cleared.";
        return;
    }

    if (currentButton) currentButton.hidden = false;
    if (actionTitle) actionTitle.textContent = "Continue Your Clearance";
    if (actionDescription) actionDescription.textContent = currentStage ? `Active stage: ${getStageLabel(currentStage)}.` : "Proceed with your uploads.";
}

/* =========================================================
   13. START / CREATE CLEARANCE (WITH CONFLICT FIX)
========================================================= */

async function startClearance() {
    const button = getElement("startClearanceButton");
    const regNo = getStudentRegNo();

    if (!regNo) {
        showToast("Student registration number missing.", "error");
        return;
    }

    setButtonLoading(button, true, "Initializing clearance...");

    try {
        const result = await requestJSON(API.clearanceCreate, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ reg_no: regNo })
        });

        const record = extractClearanceRecord(result);
        if (record) {
            clearance = record;
            sessionStorage.setItem("clearanceRecord", JSON.stringify(clearance));
        }

        await fetchClearance();

        showToast(result.message || "Clearance started successfully.", "success");
        showSection("clearance");

    } catch (error) {
        // FIX: If backend returns 409 Conflict (already started), gracefully fetch and display it!
        if (error.status === 409 || isClearanceNotFoundError(error) === false) {
            try {
                const existing = await fetchClearance();
                if (existing) {
                    renderClearance();
                    showSection("clearance");
                    showToast("Clearance record was already active. Loaded your progress.", "info");
                    return;
                }
            } catch (fetchErr) {
                console.error("Failed to load existing clearance:", fetchErr);
            }
        }

        showToast(error.message || "Unable to start clearance.", "error");
    } finally {
        setButtonLoading(button, false);
    }
}

/* =========================================================
   14. OPEN STAGE
========================================================= */

function openStage(stageKey) {
    currentViewedStage = stageKey;
    const stageSelector = getElement("documentStage");
    if (stageSelector) stageSelector.value = stageKey;

    if (!clearance) {
        showToast("Please start your clearance first.", "info");
        showSection("clearance");
        return;
    }

    showSection("documents");
    renderDocuments();
    updateUploadAvailability();
}

/* =========================================================
   15. DOCUMENT DATA HELPERS
========================================================= */

function normalizeDocument(document, stageKey = "") {
    if (!document || typeof document !== "object") return null;

    return {
        ...document,
        stage: document.stage || stageKey,
        document_name: document.document_name || document.name || "Untitled Document",
        original_filename: document.original_filename || document.filename || "",
        file_type: document.file_type || "",
        status: document.status || "under_review"
    };
}

function flattenDocuments(data) {
    if (Array.isArray(data)) return data.map(d => normalizeDocument(d)).filter(Boolean);
    if (!data || typeof data !== "object") return [];
    if (Array.isArray(data.documents)) return data.documents.map(d => normalizeDocument(d)).filter(Boolean);

    const flattened = [];
    Object.entries(data).forEach(([key, value]) => {
        if (key === "total_documents" || key === "count") return;
        if (Array.isArray(value)) {
            value.forEach(d => {
                const norm = normalizeDocument(d, key);
                if (norm) flattened.push(norm);
            });
        }
    });
    return flattened;
}

/* =========================================================
   16. FETCH DOCUMENTS
========================================================= */

async function fetchDocuments() {
    const regNo = getStudentRegNo();
    if (!regNo) return [];

    const url = new URL(API.documents);
    url.searchParams.set("reg_no", regNo);

    const result = await requestJSON(url.toString(), {
        method: "GET",
        headers: { "Accept": "application/json" },
        cache: "no-store"
    });

    const data = getResponseData(result);
    uploadedDocuments = flattenDocuments(data);
    renderDocuments();

    setText("totalDocuments", data && data.total_documents !== undefined ? data.total_documents : uploadedDocuments.length);
    return uploadedDocuments;
}

/* =========================================================
   17. RENDER DOCUMENTS TABLE
========================================================= */

function renderDocuments() {
    const tableBody = getElement("documentsTableBody");
    if (!tableBody) return;

    const docs = currentViewedStage
        ? uploadedDocuments.filter(d => d.stage === currentViewedStage)
        : uploadedDocuments;

    setText("totalDocuments", uploadedDocuments.length);

    if (docs.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="table-empty">No documents found for this stage.</td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = docs.map((doc, index) => {
        const stage = safeString(doc.stage);
        const name = safeString(doc.document_name);
        const fileType = safeString(doc.file_type || "").toUpperCase() || "FILE";
        const status = normalizeStatus(doc.status);
        const statusClass = isApproved(status) ? "status-approved" : isRejected(status) ? "status-rejected" : "status-pending";

        return `
            <tr>
                <td>
                    <div class="document-name-cell">
                        <span class="document-file-icon"><i class="fa-regular fa-file-lines"></i></span>
                        <span>${escapeHTML(name)}</span>
                    </div>
                </td>
                <td>${escapeHTML(getStageLabel(stage))}</td>
                <td>${escapeHTML(fileType)}</td>
                <td>${escapeHTML(formatDate(doc.uploaded_at || doc.created_at))}</td>
                <td><span class="status-badge ${statusClass}">${escapeHTML(humanizeStatus(status))}</span></td>
                <td>
                    <div class="table-actions">
                        <button type="button" class="table-action-button" data-document-action="view" data-document-name="${escapeHTML(name)}" data-document-stage="${escapeHTML(stage)}" title="View">
                            <i class="fa-regular fa-eye"></i>
                        </button>
                        <button type="button" class="table-action-button" data-document-action="download" data-document-name="${escapeHTML(name)}" data-document-stage="${escapeHTML(stage)}" title="Download">
                            <i class="fa-solid fa-download"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");

    tableBody.querySelectorAll("[data-document-action]").forEach(btn => {
        btn.addEventListener("click", () => {
            const name = btn.dataset.documentName;
            const stage = btn.dataset.documentStage;
            if (btn.dataset.documentAction === "view") {
                viewDocument(name, stage);
            } else {
                downloadDocument(name, stage);
            }
        });
    });
}

function viewDocument(name, stage) {
    const url = new URL(API.viewDocument);
    url.searchParams.set("reg_no", getStudentRegNo());
    url.searchParams.set("stage", stage);
    url.searchParams.set("document_name", name);
    window.open(url.toString(), "_blank", "noopener,noreferrer");
}

function downloadDocument(name, stage) {
    const url = new URL(API.downloadDocument);
    url.searchParams.set("reg_no", getStudentRegNo());
    url.searchParams.set("stage", stage);
    url.searchParams.set("document_name", name);
    window.open(url.toString(), "_blank", "noopener,noreferrer");
}

/* =========================================================
   18. UPLOAD AVAILABILITY & FORM
========================================================= */

function updateUploadAvailability() {
    const stageSelector = getElement("documentStage");
    const uploadButton = getElement("uploadDocumentButton");
    const helpText = getElement("stageUploadHelp");
    if (!stageSelector || !uploadButton) return;

    const currentStage = getCurrentStageKey();
    const selectedStage = stageSelector.value;
    const currentStatus = currentStage ? getStageStatus(currentStage) : "not_started";

    const canUpload =
        Boolean(clearance) &&
        Boolean(currentStage) &&
        selectedStage === currentStage &&
        !isClearanceCompleted() &&
        !isUnderReview(currentStatus) &&
        !isApproved(currentStatus) &&
        !uploadInProgress;

    uploadButton.disabled = !canUpload;

    if (helpText) {
        if (!clearance) helpText.textContent = "Start your clearance before uploading.";
        else if (selectedStage !== currentStage) helpText.textContent = `Select your active stage: ${getStageLabel(currentStage)}.`;
        else if (isUnderReview(currentStatus)) helpText.textContent = "Submission under review. Awaiting officer decision.";
        else if (isApproved(currentStatus)) helpText.textContent = "Stage already approved.";
        else helpText.textContent = `Ready to upload for ${getStageLabel(currentStage)}.`;
    }
}

function setupDocumentUpload() {
    const form = getElement("documentUploadForm");
    const fileInput = getElement("documentFile");
    const stageInput = getElement("documentStage");
    const uploadButton = getElement("uploadDocumentButton");
    const fileNameLabel = getElement("selectedFileName");

    if (!form) return;

    fileInput.addEventListener("change", () => {
        selectedFile = fileInput.files[0] || null;
        if (fileNameLabel) {
            fileNameLabel.textContent = selectedFile ? selectedFile.name : "Choose a file...";
        }
    });

    stageInput.addEventListener("change", () => {
        currentViewedStage = stageInput.value || null;
        updateUploadAvailability();
        renderDocuments();
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();
        if (uploadInProgress) return;

        const documentName = getElement("documentName")?.value.trim();
        const file = fileInput.files[0];
        const stage = stageInput.value;
        const regNo = getStudentRegNo();

        if (!documentName || !file || !stage) {
            showMessage("uploadMessage", "Please fill in all document fields.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("reg_no", regNo);
        formData.append("stage", stage);
        formData.append("document_name", documentName);
        formData.append("document", file);

        uploadInProgress = true;
        setButtonLoading(uploadButton, true, "Uploading...");
        showMessage("uploadMessage", "Uploading document...", "info");

        try {
            const result = await requestJSON(API.uploadDocument, {
                method: "POST",
                body: formData
            });

            showMessage("uploadMessage", result.message || "Uploaded successfully.", "success");
            showToast(result.message || "Document uploaded.", "success");
            form.reset();
            if (fileNameLabel) fileNameLabel.textContent = "No file selected.";

            await fetchClearance();
            await fetchDocuments();
        } catch (error) {
            showMessage("uploadMessage", error.message || "Upload failed.", "error");
        } finally {
            uploadInProgress = false;
            setButtonLoading(uploadButton, false);
            updateUploadAvailability();
        }
    });
}

/* =========================================================
   19. CHANGE PASSWORD & UI UTILS
========================================================= */

function setupPasswordVisibility() {
    document.querySelectorAll("[data-password-target]").forEach(btn => {
        btn.addEventListener("click", () => {
            const input = getElement(btn.dataset.passwordTarget);
            if (!input) return;
            const isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            const icon = btn.querySelector("i");
            if (icon) {
                icon.classList.toggle("fa-eye", !isPassword);
                icon.classList.toggle("fa-eye-slash", isPassword);
            }
        });
    });
}

function setupChangePassword() {
    const form = getElement("changePasswordForm");
    if (!form) return;

    form.addEventListener("submit", async event => {
        event.preventDefault();
        const currentPassword = getElement("currentPassword")?.value || "";
        const newPassword = getElement("newPassword")?.value || "";
        const confirmPassword = getElement("confirmNewPassword")?.value || "";
        const regNo = getStudentRegNo();
        const button = getElement("changePasswordButton");

        if (newPassword !== confirmPassword) {
            showMessage("passwordMessage", "New passwords do not match.", "error");
            return;
        }

        setButtonLoading(button, true, "Updating...");

        try {
            const result = await requestJSON(API.changePassword, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    reg_no: regNo,
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            showMessage("passwordMessage", result.message || "Password updated.", "success");
            showToast("Password updated successfully.", "success");
            form.reset();
        } catch (error) {
            showMessage("passwordMessage", error.message || "Failed to update password.", "error");
        } finally {
            setButtonLoading(button, false);
        }
    });
}

function setupLogout() {
    const logoutBtn = getElement("logoutButton");
    if (!logoutBtn) return;

    logoutBtn.addEventListener("click", () => {
        if (window.confirm("Are you sure you want to log out?")) {
            sessionStorage.removeItem("clearanceStudent");
            sessionStorage.removeItem("studentRegNo");
            sessionStorage.removeItem("clearanceRecord");
            window.location.replace("./index.html");
        }
    });
}

function renderCurrentDate() {
    const dateEl = getElement("currentDate");
    if (dateEl) {
        dateEl.textContent = new Date().toLocaleDateString(undefined, {
            weekday: "short", day: "numeric", month: "short", year: "numeric"
        });
    }
    setText("footerYear", new Date().getFullYear());
}

function hidePageLoader() {
    const loader = getElement("pageLoader");
    if (loader) {
        loader.classList.add("hidden");
        setTimeout(() => loader.style.display = "none", 300);
    }
}

/* =========================================================
   20. INITIALIZATION
========================================================= */

async function initializeDashboard() {
    if (!restoreStudentSession()) return;

    renderCurrentDate();
    renderStudentProfile();

    setupNavigation();
    setupSidebar();
    setupDocumentUpload();
    setupPasswordVisibility();
    setupChangePassword();
    setupLogout();

    const startBtn = getElement("startClearanceButton");
    if (startBtn) {
        startBtn.addEventListener("click", e => {
            e.preventDefault();
            startClearance();
        });
    }

    const refreshDashBtn = getElement("refreshDashboardButton");
    if (refreshDashBtn) {
        refreshDashBtn.addEventListener("click", async () => {
            setButtonLoading(refreshDashBtn, true, "Refreshing...");
            try {
                await fetchClearance();
                await fetchDocuments();
                showToast("Dashboard synchronized.", "success");
            } catch (err) {
                showToast("Refresh failed.", "error");
            } finally {
                setButtonLoading(refreshDashBtn, false);
            }
        });
    }

    showSection("overview");

    try {
        await Promise.allSettled([fetchClearance(), fetchDocuments()]);
    } catch (e) {
        console.error("Initialization sync error:", e);
    } finally {
        hidePageLoader();
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeDashboard, { once: true });
} else {
    initializeDashboard();
}