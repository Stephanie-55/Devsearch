import {
    search,
    streamSearch,
    getDocuments,
    uploadFiles,
    uploadUrl,
    compare,
    getDocumentFileURL,
    deleteDocument,
    login,
    register
} from "./api.js?v=8";


const resultsDiv = document.getElementById("results");
const searchBtn = document.getElementById("searchBtn");
const searchInput = document.getElementById("searchInput");
const viewer = document.getElementById("viewer");

const documentsList = document.getElementById("documentsList");

const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const addUrlBtn = document.getElementById("addUrlBtn");

const docsHeader = document.getElementById("docsHeader");
const docsToggleIcon = document.getElementById("docsToggleIcon");
const docsContainer = document.getElementById("docsContainer");
const docsSearchInput = document.getElementById("docsSearchInput");

const doc1 = document.getElementById("doc1");
const doc2 = document.getElementById("doc2");
const compareBtn = document.getElementById("compareBtn");

let currentStream = null;

const API_BASE = "http://127.0.0.1:8000";

/* ---------------- AUTHENTICATION ---------------- */
const authScreen = document.getElementById("authScreen");
const mainApp = document.getElementById("mainApp");
const authUsername = document.getElementById("authUsername");
const authPassword = document.getElementById("authPassword");
const authLoginBtn = document.getElementById("authLoginBtn");
const authRegisterBtn = document.getElementById("authRegisterBtn");
const authErrorMsg = document.getElementById("authErrorMsg");
const logoutBtn = document.getElementById("logoutBtn");

function checkAuth() {
    const token = localStorage.getItem("token");
    if (!token) {
        authScreen.style.display = "flex";
        mainApp.style.display = "none";
        mainApp.classList.add("hidden");
        // Hide overlay elements if active
        if (currentStream) currentStream.close();
        return false;
    }
    authScreen.style.display = "none";
    mainApp.style.display = "flex";
    mainApp.classList.remove("hidden");
    return true;
}

authLoginBtn.onclick = async () => {
    const u = authUsername.value.trim();
    const p = authPassword.value;
    if (!u || !p) return;
    
    authLoginBtn.innerText = "Authenticating...";
    authErrorMsg.innerText = "";
    try {
        const res = await login(u, p);
        if (res.access_token) {
            localStorage.setItem("token", res.access_token);
            if (checkAuth()) loadDocuments();
        } else {
            authErrorMsg.style.color = "var(--danger)";
            authErrorMsg.innerText = res.detail || "Login failed";
        }
    } catch(e) {
        authErrorMsg.style.color = "var(--danger)";
        authErrorMsg.innerText = "Network error";
    } finally {
        authLoginBtn.innerText = "Login";
    }
};

authRegisterBtn.onclick = async () => {
    const u = authUsername.value.trim();
    const p = authPassword.value;
    if (!u || !p) return;
    
    authRegisterBtn.innerText = "Registering...";
    authErrorMsg.innerText = "";
    try {
        const res = await register(u, p);
        if (res.id) {
            authErrorMsg.style.color = "var(--primary)";
            authErrorMsg.innerText = "Registration successful! Please log in.";
            authPassword.value = "";
        } else {
            authErrorMsg.style.color = "var(--danger)";
            authErrorMsg.innerText = res.detail || "Registration failed. Username may exist.";
        }
    } catch(e) {
        authErrorMsg.style.color = "var(--danger)";
        authErrorMsg.innerText = "Network error";
    } finally {
        authRegisterBtn.innerText = "Register";
    }
};

logoutBtn.onclick = () => {
    localStorage.removeItem("token");
    authUsername.value = "";
    authPassword.value = "";
    checkAuth();
};




/* ---------------- LOAD DOCUMENTS ---------------- */

async function loadDocuments() {

    const docs = await getDocuments();

    if (docs && docs.detail === "Could not validate credentials") {
        logoutBtn.click();
        return;
    }

    if (!Array.isArray(docs)) return;

    documentsList.innerHTML = "";
    doc1.innerHTML = "";
    doc2.innerHTML = "";

    docs.forEach(doc => {

        const li = document.createElement("li");
        
        const nameSpan = document.createElement("span");
        nameSpan.textContent = doc.filename;
        
        const delBtn = document.createElement("button");
        delBtn.innerHTML = "&times;";
        delBtn.style.marginLeft = "10px";
        delBtn.style.color = "red";
        delBtn.style.cursor = "pointer";
        delBtn.style.border = "none";
        delBtn.style.background = "none";
        delBtn.style.fontWeight = "bold";
        
        delBtn.onclick = async () => {
            if (confirm(`Are you sure you want to delete ${doc.filename}?`)) {
                await deleteDocument(doc.id);
                loadDocuments();
            }
        };

        li.appendChild(nameSpan);
        li.appendChild(delBtn);

        documentsList.appendChild(li);

        const option1 = document.createElement("option");
        option1.value = doc.id;
        option1.textContent = doc.filename;

        const option2 = option1.cloneNode(true);

        doc1.appendChild(option1);
        doc2.appendChild(option2);

    });

    // trigger the filter once in case there's already text in search
    docsSearchInput.dispatchEvent(new Event("input"));
}

let docsExpanded = true;

docsHeader.onclick = () => {
    docsExpanded = !docsExpanded;
    docsContainer.style.display = docsExpanded ? "block" : "none";
    docsToggleIcon.innerText = docsExpanded ? "▼" : "▶";
};

docsSearchInput.addEventListener("input", (e) => {
    const term = e.target.value.toLowerCase();
    const items = documentsList.querySelectorAll("li");
    
    items.forEach(li => {
        const name = li.querySelector("span").textContent.toLowerCase();
        li.style.display = name.includes(term) ? "flex" : "none";
    });
});

// Initial boot sequence
if (checkAuth()) {
    loadDocuments();
}



/* ---------------- SEARCH ---------------- */

searchBtn.onclick = startSearch;

searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") startSearch();
});


function startSearch() {

    const query = searchInput.value.trim();

    if (!query) return;

    resultsDiv.innerHTML = "Searching...";

    if (currentStream) {
        currentStream.close();
    }

    resultsDiv.innerHTML = "";

    currentStream = streamSearch(query, renderResult);

}



/* ---------------- RENDER RESULT ---------------- */

function renderResult(result) {

    // Auth verification fallback
    if (result.detail === "Could not validate credentials") {
        logoutBtn.click();
        return;
    }

    const card = document.createElement("div");
    card.className = "resultCard";

    const scorePercent = Math.max(0, Math.min(100, result.score * 50 + 50));

    card.innerHTML = `
        <b>${result.document}</b>
        <p class="page-indicator">Page ${result.page}</p>
        <p>${result.snippet}</p>

        <div class="scoreBar">
            <div class="scoreFill" style="width:${scorePercent}%"></div>
        </div>
    `;

    card.onclick = () => {
        const fileURL = getDocumentFileURL(result.document_id);
        const chunkText = result.content;

        if (result.document.endsWith(".txt")) {
            viewer.src = fileURL;
        } else {
            viewer.src =
                `pdfjs/web/viewer.html?file=${encodeURIComponent(fileURL)}#page=${result.page}&search=${encodeURIComponent(chunkText)}&phrase=true`;
        }
    };
    resultsDiv.appendChild(card);
}



/* ---------------- UPLOAD ---------------- */

uploadBtn.onclick = () => fileInput.click();

fileInput.onchange = async () => {

    const files = fileInput.files;

    if (!files.length) return;
    
    uploadBtn.innerText = "Uploading...";
    uploadBtn.disabled = true;

    try {
        const result = await uploadFiles(files);
        
        if (result && result.detail === "Could not validate credentials") return logoutBtn.click();

        if (result && result.detail) {
            alert(`Upload failed: ${result.detail}`);
            return;
        }
        
        alert("Upload complete");
        loadDocuments();
    } catch (e) {
        alert("An error occurred during upload.");
    } finally {
        uploadBtn.innerText = "Upload Document";
        uploadBtn.disabled = false;
        fileInput.value = "";
    }
};

addUrlBtn.onclick = async () => {
    const url = prompt("Enter a website URL to scrape and index:");
    if (!url) return;
    
    addUrlBtn.innerText = "Scraping...";
    addUrlBtn.disabled = true;
    try {
        const res = await uploadUrl(url);
        
        if (res && res.detail === "Could not validate credentials") return logoutBtn.click();
        
        if (res && res.detail) {
            alert(`Scraping failed: ${res.detail}`);
            return;
        }
        alert("Website scraped and indexed successfully!");
        loadDocuments();
    } catch(e) {
        alert("An error occurred while scraping the URL.");
    } finally {
        addUrlBtn.innerText = "Scrape Web URL";
        addUrlBtn.disabled = false;
    }
};







/* ---------------- COMPARE ---------------- */
compareBtn.onclick = async () => {

    const d1 = doc1.value;
    const d2 = doc2.value;

    if (!d1 || !d2) return;

    compareBtn.innerText = "Comparing...";
    compareBtn.disabled = true;

    const container = document.getElementById("compareResult");
    container.innerHTML = `
        <div class="progress-bar-container" style="margin-top: 20px;">
            <div class="progress-bar-track">
                <div class="progress-bar-fill"></div>
            </div>
            <p style="text-align:center; color: var(--text-muted); font-size: 13px; margin-top: 12px; font-weight: 500;">Running semantic analysis...</p>
        </div>
    `;

    try {
        const result = await compare(d1, d2);
        
        container.innerHTML = "";

        const similarity = result.similarity.toFixed(3);

        const header = document.createElement("div");
        header.innerHTML = `<h3 style="color: var(--text); font-size: 15px; margin-bottom: 12px;">Document Similarity: <span style="color: var(--primary);">${similarity}</span></h3>`;

        container.appendChild(header);

        const list = document.createElement("div");

        result.top_matches.forEach(match => {
            const card = document.createElement("div");
            card.className = "compareCard";
            card.innerHTML = `
                <b>Similarity: ${match.similarity.toFixed(3)}</b>
                <p><b>Doc A:</b> ${match.chunk_a_preview}</p>
                <p><b>Doc B:</b> ${match.chunk_b_preview}</p>
            `;
            list.appendChild(card);
        });

        container.appendChild(list);
    } catch (e) {
        container.innerHTML = `<p style="color: var(--danger); text-align: center; margin-top: 10px;">Error running comparison.</p>`;
    } finally {
        compareBtn.innerText = "Compare";
        compareBtn.disabled = false;
    }
};