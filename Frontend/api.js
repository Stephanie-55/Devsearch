const API_BASE = "http://127.0.0.1:8000";

function getHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

/* ---------------- Auth ---------------- */
export async function login(username, password) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    const res = await fetch(`${API_BASE}/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params
    });
    return res.json();
}

export async function register(username, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    return res.json();
}

/* ---------------- DOCUMENTS ---------------- */
export function getDocumentFileURL(documentId) {
    const token = localStorage.getItem("token") || "";
    return `${API_BASE}/documents/${documentId}/file?token=${token}`;
}

export async function getDocuments() {
    const res = await fetch(`${API_BASE}/documents/`, { headers: getHeaders() });
    return res.json();
}


export async function search(query, k = 5, keywords = "") {
    let url = `${API_BASE}/search/?q=${encodeURIComponent(query)}&k=${k}`;
    if (keywords) {
        url += `&keywords=${encodeURIComponent(keywords)}`;
    }
    const res = await fetch(url, { headers: getHeaders() });
    return res.json();
}


let activeStream = null;

export function streamSearch(query, onResult, k = 5, keywords = "") {

    if (activeStream) {
        activeStream.close();
    }

    let url = `${API_BASE}/search/stream?q=${encodeURIComponent(query)}&k=${k}`;
    if (keywords) {
        url += `&keywords=${encodeURIComponent(keywords)}`;
    }
    
    // Server-Sent Events don't easily support custom headers in the browser EventSource,
    // so we append the token to the URL so the backend could theoreticallly read it. 
    // But since the backend expects Depends(oauth2_proxy), standard EventSource will fail authentication.
    // However, since we aren't using the stream heavily right now, we can pass it as a query param if backend supported it, 
    // or just fetch polyfill. For now, since SSE doesn't accept headers, we will polyfill it with fetch:
    
    const stream = {
        close: () => {}
    };
    
    fetch(url, { headers: getHeaders() }).then(async response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");
            for (let line of lines) {
                if (line.startsWith("data: ")) {
                    const dataStr = line.slice(6);
                    if (dataStr === "done") return;
                    try {
                        onResult(JSON.parse(dataStr));
                    } catch(e) {}
                }
            }
        }
    });
    
    activeStream = stream; // Update activeStream to the new stream object

    return stream;
}


export async function uploadFiles(files) {

    const form = new FormData();

    for (let file of files) {
        form.append("files", file);
    }

    const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        headers: getHeaders(), // Fetch automatically sets multipart/form-data when passing FormData!
        body: form
    });

    return res.json();
}

export async function uploadUrl(url) {
    const res = await fetch(`${API_BASE}/upload/url`, {
        method: "POST",
        headers: { ...getHeaders(), "Content-Type": "application/json" },
        body: JSON.stringify({ url })
    });
    return res.json();
}


export async function compare(docA, docB) {
    const res = await fetch(
        `${API_BASE}/compare/?doc_a=${docA}&doc_b=${docB}&k=5`,
        { headers: getHeaders() }
    );
    return res.json();
}

export async function buildIndex() {
    const res = await fetch(`${API_BASE}/index/rebuild`, {
        method: "POST",
        headers: getHeaders()
    });
    return res.json();
}

export async function deleteDocument(documentId) {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
        method: "DELETE",
        headers: getHeaders()
    });
    return res.json();
}