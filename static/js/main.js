// Every dashboard page sets window.API_TOKEN to a short-lived JWT
// (issued server-side at page render). All dynamic actions below call
// the JSON REST API in api.py directly from the browser using that
// token, instead of doing a full page reload.

async function apiFetch(url, options = {}) {
    const headers = Object.assign(
        { "Content-Type": "application/json" },
        options.headers || {},
        window.API_TOKEN ? { Authorization: `Bearer ${window.API_TOKEN}` } : {}
    );
    const res = await fetch(url, { ...options, headers });
    let body = null;
    try { body = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) {
        throw new Error((body && body.error) || `Request failed (${res.status})`);
    }
    return body;
}

document.addEventListener("DOMContentLoaded", () => {

    // ---- Enroll button (student dashboard + course detail page) ----
    document.querySelectorAll(".enroll-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const courseId = btn.dataset.courseId;
            btn.disabled = true;
            btn.textContent = "Enrolling...";
            try {
                await apiFetch(`/api/courses/${courseId}/enroll`, { method: "POST" });
                location.reload();
            } catch (err) {
                alert(err.message);
                btn.disabled = false;
                btn.textContent = "Enroll";
            }
        });
    });

    // ---- Create course form (instructor dashboard) ----
    const createCourseForm = document.getElementById("create-course-form");
    if (createCourseForm) {
        createCourseForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const msg = document.getElementById("create-course-msg");
            const formData = new FormData(createCourseForm);
            try {
                await apiFetch("/api/courses", {
                    method: "POST",
                    body: JSON.stringify({
                        title: formData.get("title"),
                        description: formData.get("description"),
                    }),
                });
                location.reload();
            } catch (err) {
                msg.textContent = err.message;
                msg.style.color = "var(--error)";
            }
        });
    }

    // ---- Create lesson form (course detail page, instructor/admin) ----
    const createLessonForm = document.getElementById("create-lesson-form");
    if (createLessonForm) {
        createLessonForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const courseId = createLessonForm.dataset.courseId;
            const formData = new FormData(createLessonForm);
            try {
                await apiFetch(`/api/courses/${courseId}/lessons`, {
                    method: "POST",
                    body: JSON.stringify({
                        title: formData.get("title"),
                        content: formData.get("content"),
                        order_index: parseInt(formData.get("order_index"), 10) || 0,
                    }),
                });
                location.reload();
            } catch (err) {
                alert(err.message);
            }
        });
    }

    // ---- Delete lesson buttons ----
    document.querySelectorAll(".delete-lesson-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            if (!confirm("Delete this lesson?")) return;
            try {
                await apiFetch(`/api/lessons/${btn.dataset.lessonId}`, { method: "DELETE" });
                location.reload();
            } catch (err) {
                alert(err.message);
            }
        });
    });

    // ---- Progress slider (student, course detail page) ----
    const slider = document.getElementById("progress-slider");
    if (slider) {
        const valueLabel = document.getElementById("progress-value");
        slider.addEventListener("input", () => {
            valueLabel.textContent = `${slider.value}%`;
        });
        slider.addEventListener("change", async () => {
            try {
                await apiFetch(`/api/enrollments/${slider.dataset.courseId}/progress`, {
                    method: "PATCH",
                    body: JSON.stringify({ progress: parseInt(slider.value, 10) }),
                });
            } catch (err) {
                alert(err.message);
            }
        });
    }

    // ---- Role change select (admin: manage users page) ----
    document.querySelectorAll(".role-select").forEach((select) => {
        select.addEventListener("change", async () => {
            const userId = select.dataset.userId;
            try {
                await apiFetch(`/api/users/${userId}/role`, {
                    method: "PATCH",
                    body: JSON.stringify({ role: select.value }),
                });
            } catch (err) {
                alert(err.message);
                location.reload();
            }
        });
    });
});
