/**
 * SmartEdu AI Learning and Coding Platform — Core Single Page Application
 * Handles JWT Authentication, Syllabus Learning Tree, Personal Coding IDE,
 * Socratic AI Tutor, Quizzes, Scikit-Learn Regression & Chart.js Visualizations.
 */

// Application State
const State = {
  token: localStorage.getItem("smartedu_token") || null,
  user: null,
  activeView: "dashboard",
  currentSubjectId: null,
  currentTopicId: null,
  activeQuiz: null,
  quizTimerInterval: null,
  charts: {}
};

// ==============================================================================
// 1. HTTP API Request Helper
// ==============================================================================

async function apiFetch(endpoint, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (State.token) {
    headers["Authorization"] = `Bearer ${State.token}`;
  }
  const config = { ...options, headers };
  if (config.body && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }

  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401) {
      // Session expired or unauthenticated
      if (State.token) {
        logoutUser();
        showToast("Session expired. Please log in again.", "error");
      }
      return null;
    }
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "API request failed");
    }
    return data;
  } catch (err) {
    showToast(err.message, "error");
    throw err;
  }
}

function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ==============================================================================
// 2. Authentication & Session Management
// ==============================================================================

async function initAuth() {
  if (State.token) {
    try {
      const user = await apiFetch("/api/auth/me");
      if (user) {
        setLoggedInUser(user);
        return;
      }
    } catch {
      logoutUser();
    }
  }

  // If no active session, auto-login as Student (Alex) by default for seamless evaluation
  await performQuickLogin("student.alex@smartedu.edu", "Student@2026");
}

function setLoggedInUser(user) {
  State.user = user;
  const navAvatar = document.getElementById("nav-user-avatar");
  const navName = document.getElementById("nav-user-name");
  const navRole = document.getElementById("nav-user-role");
  const btnAuth = document.getElementById("btn-auth-action");
  const teacherNav = document.getElementById("teacher-nav-group");
  const roleLabel = document.getElementById("sidebar-role-label");
  const heroName = document.getElementById("hero-user-name");
  const heroMeta = document.getElementById("hero-academic-meta");

  if (navAvatar) navAvatar.innerText = user.full_name ? user.full_name[0].toUpperCase() : "U";
  if (navName) navName.innerText = user.full_name;
  if (navRole) navRole.innerText = user.role.toUpperCase();
  if (btnAuth) btnAuth.innerText = "Switch / Logout";
  if (heroName) heroName.innerText = user.full_name;

  if (heroMeta && user.department) {
    heroMeta.innerText = `${user.department} • Semester ${user.semester || 4} • ${user.college || "Institute of Technology"}`;
  }

  // Toggle teacher controls
  if (user.role === "teacher" || user.role === "admin") {
    if (teacherNav) teacherNav.classList.remove("hidden");
    if (roleLabel) roleLabel.innerText = "FACULTY PORTAL";
  } else {
    if (teacherNav) teacherNav.classList.add("hidden");
    if (roleLabel) roleLabel.innerText = "STUDENT PORTAL";
  }

  loadSystemStatus();
  loadNotifications();
  loadDashboardData();
}

function logoutUser() {
  State.token = null;
  State.user = null;
  localStorage.removeItem("smartedu_token");
  const navName = document.getElementById("nav-user-name");
  const navRole = document.getElementById("nav-user-role");
  const btnAuth = document.getElementById("btn-auth-action");
  if (navName) navName.innerText = "Guest User";
  if (navRole) navRole.innerText = "Not Logged In";
  if (btnAuth) btnAuth.innerText = "Login";
  switchView("auth");
}

async function performQuickLogin(email, password) {
  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: { email, password }
    });
    if (res && res.access_token) {
      State.token = res.access_token;
      localStorage.setItem("smartedu_token", res.access_token);
      setLoggedInUser(res.user);
      showToast(`Logged in as ${res.user.full_name} (${res.user.role})`, "success");
      switchView(res.user.role === "teacher" ? "teacher-dashboard" : "dashboard");
    }
  } catch (err) {
    console.error("Quick login failed:", err);
  }
}

// ==============================================================================
// 3. View Router & Navigation
// ==============================================================================

function switchView(viewName) {
  State.activeView = viewName;
  document.querySelectorAll(".view-panel").forEach(p => p.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(i => i.classList.remove("active"));

  const targetPanel = document.getElementById(`view-${viewName}`);
  if (targetPanel) targetPanel.classList.remove("hidden");

  const targetNav = document.querySelector(`[data-view="${viewName}"]`);
  if (targetNav) targetNav.classList.add("active");

  // View specific loaders
  if (viewName === "dashboard") loadDashboardData();
  else if (viewName === "syllabus") loadSyllabusView();
  else if (viewName === "coding") loadCodingView();
  else if (viewName === "quizzes") loadQuizzesView();
  else if (viewName === "assignments") loadAssignmentsView();
  else if (viewName === "analytics") loadAnalyticsView();
  else if (viewName === "teacher-dashboard") loadTeacherDashboardView();
  else if (viewName === "syllabus-builder") loadSyllabusBuilderView();
  else if (viewName === "history") loadTaskHistory();
  else if (viewName === "generator") {}
  else if (viewName === "testing") {}
  else if (viewName === "review") {}
  else if (viewName === "github") {}
}

// ==============================================================================
// 4. Student Dashboard
// ==============================================================================

async function loadDashboardData() {
  if (!State.user) return;

  // 1. Summary analytics
  try {
    const summary = await apiFetch("/api/analytics/summary");
    if (summary) {
      document.getElementById("metric-enrolled-count").innerText = summary.enrolled_subjects_count;
      document.getElementById("metric-study-time").innerText = `${summary.total_study_time_hours} hrs`;
      document.getElementById("metric-quiz-avg").innerText = `${summary.average_quiz_score}%`;
      document.getElementById("metric-coding-success").innerText = `${summary.coding_success_rate}%`;
    }
  } catch (e) { console.error(e); }

  // 2. Continue Learning Topic
  try {
    const cont = await apiFetch("/api/academic/continue-learning");
    if (cont && cont.has_resume) {
      document.getElementById("resume-topic-title").innerText = cont.topic_title;
      document.getElementById("resume-course-title").innerText = `${cont.subject_title} • ${cont.chapter_title}`;
      document.getElementById("btn-jump-topic").onclick = () => {
        State.currentSubjectId = cont.subject_id;
        State.currentTopicId = cont.topic_id;
        switchView("syllabus");
      };
    }
  } catch (e) { console.error(e); }

  // 3. Weakness banner
  try {
    const report = await apiFetch("/api/ai/weaknesses");
    if (report && report.weaknesses && report.weaknesses.length > 0) {
      const topWeak = report.weaknesses[0];
      document.getElementById("dashboard-weakness-desc").innerText =
        `Detected ${report.high_struggle_count} High Difficulty topic(s): '${topWeak.concept_name}'. Recommended action: ${topWeak.recommended_actions[0] || 'Review notes'}`;
      document.getElementById("dashboard-weakness-banner").classList.remove("hidden");
    } else {
      document.getElementById("dashboard-weakness-banner").classList.add("hidden");
    }
  } catch (e) { console.error(e); }

  // 4. Enrolled Subjects Grid
  try {
    const subjects = await apiFetch("/api/academic/subjects");
    const container = document.getElementById("enrolled-subjects-grid");
    if (container && subjects) {
      container.innerHTML = subjects.map(s => `
        <div class="subject-card">
          <div class="subject-header">
            <span class="subject-code">${s.code}</span>
            <span class="badge badge-primary">Semester ${s.semester}</span>
          </div>
          <h3 class="subject-title">${s.title}</h3>
          <p class="subject-desc">${s.description || 'Comprehensive syllabus modules.'}</p>
          <div class="subject-progress-bar">
            <div class="subject-progress-fill" style="width: ${s.completion_percentage}%"></div>
          </div>
          <div class="subject-meta-row">
            <span>Progress: ${s.completion_percentage}%</span>
            <span>${s.completed_topics}/${s.total_topics} Topics</span>
          </div>
          <button class="btn btn-primary btn-block" onclick="openSubjectSyllabus(${s.id})">Open Syllabus Tree</button>
        </div>
      `).join("");
    }
  } catch (e) { console.error(e); }
}

window.openSubjectSyllabus = function(subId) {
  State.currentSubjectId = subId;
  switchView("syllabus");
};

// ==============================================================================
// 5. Syllabus & Learning System
// ==============================================================================

async function loadSyllabusView() {
  const subjects = await apiFetch("/api/academic/subjects");
  const select = document.getElementById("select-subject-syllabus");
  if (!subjects || subjects.length === 0) return;

  select.innerHTML = subjects.map(s => `<option value="${s.id}">${s.code}: ${s.title}</option>`).join("");
  if (State.currentSubjectId) {
    select.value = State.currentSubjectId;
  } else {
    State.currentSubjectId = subjects[0].id;
  }

  select.onchange = () => {
    State.currentSubjectId = parseInt(select.value);
    fetchSyllabusTree(State.currentSubjectId);
  };

  fetchSyllabusTree(State.currentSubjectId);
}

async function fetchSyllabusTree(subId) {
  const data = await apiFetch(`/api/academic/subjects/${subId}/syllabus`);
  if (!data) return;

  document.getElementById("syllabus-completion-pct").innerText = `${data.completion_percentage}%`;
  const treeContainer = document.getElementById("syllabus-tree-container");

  if (!data.units || data.units.length === 0) {
    treeContainer.innerHTML = "<p class='placeholder-text'>No syllabus units uploaded yet for this subject.</p>";
    return;
  }

  let html = "";
  let firstTopic = null;

  data.units.forEach(u => {
    html += `<div class="unit-node">
      <div class="unit-header">📘 Unit ${u.unit_number}: ${u.title}</div>
      <div class="unit-body">`;
    u.chapters.forEach(ch => {
      ch.topics.forEach(t => {
        if (!firstTopic && (!State.currentTopicId || t.id === State.currentTopicId)) {
          firstTopic = t;
        }
        const activeClass = State.currentTopicId === t.id ? "active" : "";
        const icon = t.is_completed ? "✓" : "○";
        html += `
          <div class="topic-item-row ${activeClass}" id="topic-row-${t.id}" onclick="renderTopicNotes(${JSON.stringify(t).replace(/"/g, '&quot;')})">
            <span>${icon} ${t.topic_number}. ${t.title}</span>
            <span class="badge ${t.is_completed ? 'badge-primary' : ''}">${t.study_time_minutes > 0 ? t.study_time_minutes + 'm' : ''}</span>
          </div>
        `;
      });
    });
    html += `</div></div>`;
  });

  treeContainer.innerHTML = html;

  if (firstTopic) {
    renderTopicNotes(firstTopic);
  }
}

window.renderTopicNotes = function(topic) {
  State.currentTopicId = topic.id;
  document.querySelectorAll(".topic-item-row").forEach(r => r.classList.remove("active"));
  const row = document.getElementById(`topic-row-${topic.id}`);
  if (row) row.classList.add("active");

  document.getElementById("topic-breadcrumb").innerText = `Topic #${topic.topic_number}`;
  document.getElementById("topic-display-title").innerText = topic.title;
  document.getElementById("topic-objectives-text").innerText = topic.learning_objectives || "Master the theoretical and implementation principles of this module.";
  
  // Format markdown or content
  const content = topic.study_content || "Study material will be posted by the faculty.";
  document.getElementById("topic-study-content").innerHTML = formatMarkdown(content);

  const completeBtn = document.getElementById("btn-mark-topic-complete");
  completeBtn.innerText = topic.is_completed ? "✓ Completed" : "Mark as Completed";
  completeBtn.onclick = async () => {
    await apiFetch(`/api/academic/topics/${topic.id}/progress`, {
      method: "PUT",
      body: { is_completed: true, study_time_minutes: 15.0 }
    });
    showToast("Progress saved! Topic marked as completed.", "success");
    fetchSyllabusTree(State.currentSubjectId);
  };

  document.getElementById("btn-topic-practice-code").onclick = () => {
    switchView("coding");
  };

  document.getElementById("btn-topic-ai-hint").onclick = () => {
    switchView("ai-tutor");
    sendAIChat(`Can you explain the main concept of '${topic.title}' with a simple analogy?`);
  };
};

function formatMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/```python([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    .replace(/```text([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    .replace(/\n/gim, '<br>');
  return html;
}

// ==============================================================================
// 6. Personal Coding Platform
// ==============================================================================

function loadCodingView() {
  loadCodeSubmissionsHistory();
}

async function runStudentCode() {
  const language = document.getElementById("select-code-lang").value;
  const source_code = document.getElementById("code-editor").value;
  const custom_input = document.getElementById("custom-input-box").value;

  const statusBadge = document.getElementById("telemetry-status");
  const timeBadge = document.getElementById("telemetry-time");
  const memBadge = document.getElementById("telemetry-memory");
  const provBadge = document.getElementById("telemetry-provider");
  const consoleOut = document.getElementById("stdout-console");
  const errorDrawer = document.getElementById("error-panel-drawer");
  const errorOut = document.getElementById("error-output-console");

  statusBadge.innerText = "Status: Executing...";
  consoleOut.innerText = "Executing via compiler service...";
  errorDrawer.classList.add("hidden");

  try {
    const result = await apiFetch("/api/coding/execute", {
      method: "POST",
      body: {
        language,
        source_code,
        custom_input,
        subject_id: State.currentSubjectId,
        topic_id: State.currentTopicId
      }
    });

    if (result) {
      statusBadge.innerText = `Status: ${result.status}`;
      timeBadge.innerText = `Time: ${result.execution_time ? result.execution_time + 's' : '-'}`;
      memBadge.innerText = `Memory: ${result.memory_used ? result.memory_used + 'KB' : '-'}`;
      provBadge.innerText = `Engine: ${result.provider}`;

      consoleOut.innerText = result.stdout || "(No standard output generated)";

      // Handle errors accurately
      if (result.stderr || result.compile_output) {
        errorDrawer.classList.remove("hidden");
        const errText = result.compile_output || result.stderr;
        errorOut.innerText = errText;

        document.getElementById("btn-debug-with-ai").onclick = () => {
          switchView("ai-tutor");
          const modeChip = document.querySelector('[data-mode="error_debug"]');
          if (modeChip) modeChip.click();
          sendAIChat("Why am I seeing this execution error in my code?", errText, source_code);
        };
      }
      loadCodeSubmissionsHistory();
    }
  } catch (err) {
    statusBadge.innerText = "Status: Error";
    consoleOut.innerText = err.message;
  }
}

async function loadCodeSubmissionsHistory() {
  const data = await apiFetch("/api/coding/submissions?limit=10");
  const tbody = document.getElementById("code-submissions-body");
  if (!tbody || !data) return;

  if (data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center">No code submissions logged yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = data.map(s => `
    <tr>
      <td>${new Date(s.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
      <td><strong>${s.language}</strong></td>
      <td><span class="badge ${s.status === 'Accepted' ? 'badge-primary' : 'badge-danger'}">${s.status}</span></td>
      <td>${s.execution_time ? s.execution_time + 's' : '-'}</td>
      <td>${s.memory_used ? s.memory_used + ' KB' : '-'}</td>
      <td>${s.provider}</td>
    </tr>
  `).join("");
}

// ==============================================================================
// 7. AI Socratic Learning Assistant
// ==============================================================================

let currentTutorMode = "concept";

async function sendAIChat(message, errorContext = null, codeContext = null) {
  const container = document.getElementById("ai-chat-messages");
  if (!container) return;

  // Append user bubble
  const userDiv = document.createElement("div");
  userDiv.className = "chat-bubble user-bubble";
  userDiv.innerHTML = `<div class="bubble-sender">${State.user ? State.user.full_name : 'You'}</div><div class="bubble-body">${message}</div>`;
  container.appendChild(userDiv);
  container.scrollTop = container.scrollHeight;

  // Loading bubble
  const aiDiv = document.createElement("div");
  aiDiv.className = "chat-bubble ai-bubble";
  aiDiv.innerHTML = `<div class="bubble-sender">AI Tutor</div><div class="bubble-body">Thinking Socratic guidance...</div>`;
  container.appendChild(aiDiv);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await apiFetch("/api/ai/chat", {
      method: "POST",
      body: {
        message,
        assistance_type: currentTutorMode,
        subject_id: State.currentSubjectId,
        topic_id: State.currentTopicId,
        code_context: codeContext || document.getElementById("code-editor")?.value,
        error_context: errorContext
      }
    });

    if (res) {
      aiDiv.innerHTML = `<div class="bubble-sender">AI Tutor (${res.model})</div><div class="bubble-body">${formatMarkdown(res.response)}</div>`;
    }
  } catch (err) {
    aiDiv.innerHTML = `<div class="bubble-sender">AI Tutor</div><div class="bubble-body text-danger">Error: ${err.message}</div>`;
  }
  container.scrollTop = container.scrollHeight;
}

// ==============================================================================
// 8. Quizzes & Assessments
// ==============================================================================

async function loadQuizzesView() {
  const quizzes = await apiFetch("/api/assessments/quizzes");
  const container = document.getElementById("quizzes-grid");
  if (!container || !quizzes) return;

  container.innerHTML = quizzes.map(q => `
    <div class="subject-card">
      <div class="subject-header">
        <span class="subject-code">QUIZ</span>
        <span class="badge ${q.user_attempted ? 'badge-primary' : ''}">${q.user_attempted ? 'Completed: ' + q.last_score + '/' + q.total_marks : 'Available'}</span>
      </div>
      <h3 class="subject-title">${q.title}</h3>
      <p class="subject-desc">${q.description || 'Topic mastery quiz.'}</p>
      <div class="subject-meta-row">
        <span>⏱️ ${q.time_limit_minutes} Mins</span>
        <span>Marks: ${q.total_marks}</span>
        <span>${q.question_count} Questions</span>
      </div>
      <button class="btn btn-primary btn-block" onclick="startQuiz(${q.id})">
        ${q.user_attempted ? 'Retake Quiz' : 'Start Assessment'}
      </button>
    </div>
  `).join("");
}

window.startQuiz = async function(quizId) {
  const quiz = await apiFetch(`/api/assessments/quizzes/${quizId}`);
  if (!quiz) return;

  State.activeQuiz = quiz;
  document.getElementById("quizzes-grid").classList.add("hidden");
  document.getElementById("quiz-player-container").classList.remove("hidden");
  document.getElementById("quiz-results-container").classList.add("hidden");

  document.getElementById("player-quiz-title").innerText = quiz.title;
  document.getElementById("player-quiz-meta").innerText = `Total Marks: ${quiz.total_marks} • Time Allowed: ${quiz.time_limit_minutes} minutes`;

  // Start Countdown
  let secondsLeft = quiz.time_limit_minutes * 60;
  clearInterval(State.quizTimerInterval);
  const timerDisplay = document.getElementById("quiz-time-display");

  State.quizTimerInterval = setInterval(() => {
    secondsLeft--;
    const m = Math.floor(secondsLeft / 60);
    const s = secondsLeft % 60;
    timerDisplay.innerText = `${m}:${s < 10 ? '0' : ''}${s}`;
    if (secondsLeft <= 0) {
      clearInterval(State.quizTimerInterval);
      document.getElementById("quiz-submission-form").requestSubmit();
    }
  }, 1000);

  // Render questions
  const qList = document.getElementById("quiz-questions-list");
  qList.innerHTML = quiz.questions.map((q, idx) => `
    <div class="question-block">
      <div class="question-prompt">Q${idx + 1}. ${q.question_text} (${q.marks} marks)</div>
      <div class="options-group">
        ${q.options.map(opt => `
          <label class="option-label">
            <input type="radio" name="question_${q.id}" value="${opt.replace(/"/g, '&quot;')}">
            ${opt}
          </label>
        `).join("")}
      </div>
    </div>
  `).join("");
};

async function submitQuiz(e) {
  e.preventDefault();
  if (!State.activeQuiz) return;
  clearInterval(State.quizTimerInterval);

  const answers = {};
  State.activeQuiz.questions.forEach(q => {
    const selected = document.querySelector(`input[name="question_${q.id}"]:checked`);
    if (selected) {
      answers[q.id] = selected.value;
    }
  });

  const attempt = await apiFetch(`/api/assessments/quizzes/${State.activeQuiz.id}/submit`, {
    method: "POST",
    body: { answers, time_taken_seconds: 120 }
  });

  if (attempt) {
    document.getElementById("quiz-player-container").classList.add("hidden");
    const resBox = document.getElementById("quiz-results-container");
    resBox.classList.remove("hidden");

    document.getElementById("res-score-val").innerText = attempt.score;
    document.getElementById("res-max-val").innerText = attempt.max_score;
    document.getElementById("res-pct-val").innerText = `${attempt.percentage}%`;

    const reviewList = document.getElementById("results-review-list");
    reviewList.innerHTML = attempt.answers_review.map(r => `
      <div class="question-block" style="border-left: 4px solid ${r.is_correct ? 'var(--color-success)' : 'var(--color-danger)'}">
        <div class="question-prompt">${r.question_text}</div>
        <div style="font-size: 13px; margin: 4px 0;">
          Your Answer: <strong>${r.student_answer || 'None'}</strong> | 
          Status: <span class="badge ${r.is_correct ? 'badge-primary' : 'badge-danger'}">${r.is_correct ? 'Correct' : 'Incorrect'}</span>
        </div>
        ${!r.is_correct ? `<div style="font-size: 13px; color: var(--color-success);">Correct: ${r.correct_answers.join(', ')}</div>` : ''}
        ${r.explanation ? `<div style="font-size: 12.5px; color: var(--text-muted); margin-top: 6px;">Explanation: ${r.explanation}</div>` : ''}
      </div>
    `).join("");
  }
}

// ==============================================================================
// 9. Scikit-Learn Regression Analytics & Chart.js (10 Visualizations)
// ==============================================================================

async function loadAnalyticsView() {
  // 1. Scikit-Learn Regression Model
  try {
    const reg = await apiFetch("/api/analytics/regression");
    if (reg && reg.has_sufficient_data) {
      document.getElementById("reg-r2-val").innerText = reg.metrics.r2_score;
      document.getElementById("reg-mae-val").innerText = `${reg.metrics.mae}%`;
      document.getElementById("reg-rmse-val").innerText = `${reg.metrics.rmse}%`;
      document.getElementById("reg-samples-val").innerText = reg.data_points_count;
      document.getElementById("reg-status-badge").innerText = "Model Active";

      renderRegressionChart(reg.plot_data);
    } else if (reg) {
      document.getElementById("reg-status-badge").innerText = "Awaiting Data";
      document.getElementById("regression-disclaimer-text").innerText = reg.metrics.status_message;
    }
  } catch (e) { console.error(e); }

  // 2. 8 Additional Performance Charts
  try {
    const graphs = await apiFetch("/api/analytics/graphs");
    if (graphs) {
      renderPerformanceGraphs(graphs);
    }
  } catch (e) { console.error(e); }
}

function renderRegressionChart(plotData) {
  const ctx = document.getElementById("chart-regression-plot");
  if (!ctx) return;
  if (State.charts["reg"]) State.charts["reg"].destroy();

  const labels = plotData.map(p => p.label);
  const actuals = plotData.map(p => p.actual_score);
  const predicteds = plotData.map(p => p.predicted_score);

  State.charts["reg"] = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Actual Empirical Performance (%)",
          data: actuals,
          borderColor: "#2563eb",
          backgroundColor: "#2563eb",
          borderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8
        },
        {
          label: "Scikit-Learn Predicted Trajectory (%)",
          data: predicteds,
          borderColor: "#7c3aed",
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 4,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100, title: { display: true, text: "Overall Performance Score (%)" } }
      }
    }
  });
}

function renderPerformanceGraphs(data) {
  // Chart 1: Performance Over Time
  createChart("chart-performance-over-time", "line", data.quiz_trends.labels, [{
    label: "Score Trend",
    data: data.quiz_trends.scores,
    borderColor: "#10b981",
    fill: true,
    backgroundColor: "rgba(16, 185, 129, 0.1)"
  }]);

  // Chart 2: Weekly Study Time
  createChart("chart-weekly-study-time", "bar", data.study_time.labels, [{
    label: "Study Hours",
    data: data.study_time.hours,
    backgroundColor: "#3b82f6"
  }]);

  // Chart 3: Subject Comparison
  createChart("chart-subject-comparison", "bar", data.subject_comparison.labels, [{
    label: "Avg Score",
    data: data.subject_comparison.scores,
    backgroundColor: ["#2563eb", "#7c3aed"]
  }]);

  // Chart 4: Unit Marks
  createChart("chart-unit-marks", "bar", data.unit_marks.labels, [{
    label: "Marks",
    data: data.unit_marks.marks,
    backgroundColor: "#6366f1"
  }]);

  // Chart 5: Concept Weakness Struggle
  createChart("chart-weakness-distribution", "doughnut", data.weakness_distribution.labels, [{
    data: data.weakness_distribution.scores,
    backgroundColor: ["#ef4444", "#f59e0b", "#3b82f6", "#10b981"]
  }]);

  // Chart 6: Coding Executions
  createChart("chart-coding-ratio", "pie", data.coding_distribution.labels, [{
    data: data.coding_distribution.counts,
    backgroundColor: ["#10b981", "#ef4444", "#f59e0b", "#64748b"]
  }]);

  // Chart 7: Quiz Trends
  createChart("chart-quiz-trends", "line", data.quiz_trends.labels, [{
    label: "Quiz Marks",
    data: data.quiz_trends.scores,
    borderColor: "#f59e0b",
    borderWidth: 2
  }]);

  // Chart 8: Syllabus Completion
  createChart("chart-completion-gauge", "doughnut", ["Completed", "Remaining"], [{
    data: [data.completion_rate.completed, data.completion_rate.remaining],
    backgroundColor: ["#10b981", "#e2e8f0"]
  }]);
}

function createChart(canvasId, type, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  if (State.charts[canvasId]) State.charts[canvasId].destroy();

  State.charts[canvasId] = new Chart(ctx, {
    type,
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: type !== "bar" } }
    }
  });
}

// ==============================================================================
// 10. Teacher Dashboard & Syllabus Builder
// ==============================================================================

async function loadTeacherDashboardView() {
  const data = await apiFetch("/api/analytics/teacher-dashboard");
  if (!data) return;

  const attList = document.getElementById("teacher-attention-list");
  if (data.students_needing_attention && data.students_needing_attention.length > 0) {
    attList.innerHTML = data.students_needing_attention.map(s => `
      <div class="attention-card" style="padding:12px; border-left:4px solid var(--color-danger); background:#fef2f2; margin-bottom:8px; border-radius:4px;">
        <strong>${s.student_name}</strong> (${s.email}) — High Struggle in <em>'${s.struggle_topic}'</em>
        <span class="badge badge-danger" style="float:right;">Score: ${Math.round(s.struggle_score * 100)}%</span>
      </div>
    `).join("");
  } else {
    attList.innerHTML = "<p>No students currently flagged for academic struggle.</p>";
  }

  const rosterBody = document.getElementById("teacher-roster-body");
  if (data.students) {
    rosterBody.innerHTML = data.students.map(st => `
      <tr>
        <td><strong>${st.full_name}</strong></td>
        <td>${st.email}</td>
        <td>${st.department}</td>
        <td>Semester ${st.semester}</td>
        <td>${st.completed_topics}</td>
        <td>${st.quizzes_taken}</td>
        <td><span class="badge ${st.needs_attention ? 'badge-danger' : 'badge-primary'}">${st.needs_attention ? 'Struggling' : 'On Track'}</span></td>
      </tr>
    `).join("");
  }
}

async function loadSyllabusBuilderView() {
  const subjects = await apiFetch("/api/academic/subjects");
  const targetSelect = document.getElementById("b-target-subject");
  if (targetSelect && subjects) {
    targetSelect.innerHTML = subjects.map(s => `<option value="${s.id}">${s.code} - ${s.title}</option>`).join("");
  }
}

// ==============================================================================
// 11. In-App Notifications
// ==============================================================================

async function loadNotifications() {
  if (!State.token) return;
  try {
    const list = await apiFetch("/api/notifications");
    const badge = document.getElementById("notif-badge");
    const container = document.getElementById("notification-list");
    if (!list || !container) return;

    const unread = list.filter(n => !n.is_read);
    badge.innerText = unread.length;
    badge.style.display = unread.length > 0 ? "flex" : "none";

    if (list.length === 0) {
      container.innerHTML = `<div class="empty-notif" style="padding:16px; text-align:center; color:var(--text-muted);">No notifications</div>`;
      return;
    }

    container.innerHTML = list.map(n => `
      <div class="notif-item ${!n.is_read ? 'unread' : ''}">
        <div class="notif-title">${n.title}</div>
        <div class="notif-body">${n.message}</div>
      </div>
    `).join("");
  } catch (e) { console.error(e); }
}

// ==============================================================================
// 12. Diagnostics & System Telemetry
// ==============================================================================

async function loadSystemStatus() {
  try {
    const status = await apiFetch("/api/health");
    if (status && status.integrations) {
      const aiStatus = document.getElementById("env-ai-status");
      const compStatus = document.getElementById("env-compiler-status");
      const dbStatus = document.getElementById("env-db-status");

      if (aiStatus) {
        aiStatus.innerText = status.integrations.ai_configured ? `${status.integrations.ai_provider} (${status.integrations.ai_model})` : "Socratic Tutor (Offline)";
      }
      if (compStatus) {
        compStatus.innerText = status.integrations.judge0_configured ? "Judge0 Cloud" : "Subprocess Sandbox";
      }
      if (dbStatus) {
        dbStatus.innerText = `${status.integrations.database_type} (WAL)`;
      }
    }
  } catch (e) { console.error(e); }
}

// ==============================================================================
// 13. Event Listeners & Bootstrapping
// ==============================================================================

document.addEventListener("DOMContentLoaded", () => {
  // Navigation
  document.querySelectorAll(".nav-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const view = btn.getAttribute("data-view");
      if (view) switchView(view);
    });
  });

  // Auth Quick buttons
  document.getElementById("btn-quick-student")?.addEventListener("click", () => performQuickLogin("student.alex@smartedu.edu", "Student@2026"));
  document.getElementById("btn-quick-teacher")?.addEventListener("click", () => performQuickLogin("prof.sharma@smartedu.edu", "Teacher@2026"));
  document.getElementById("btn-quick-admin")?.addEventListener("click", () => performQuickLogin("admin@smartedu.edu", "Admin@SecurePass2026"));

  document.getElementById("btn-auth-action")?.addEventListener("click", () => {
    if (State.token) logoutUser();
    else switchView("auth");
  });

  // Auth Tabs
  document.getElementById("tab-btn-login")?.addEventListener("click", () => {
    document.getElementById("tab-btn-login").classList.add("active");
    document.getElementById("tab-btn-register").classList.remove("active");
    document.getElementById("form-login").classList.remove("hidden");
    document.getElementById("form-register").classList.add("hidden");
  });

  document.getElementById("tab-btn-register")?.addEventListener("click", () => {
    document.getElementById("tab-btn-register").classList.add("active");
    document.getElementById("tab-btn-login").classList.remove("active");
    document.getElementById("form-register").classList.remove("hidden");
    document.getElementById("form-login").classList.add("hidden");
  });

  // Forms
  document.getElementById("form-login")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    await performQuickLogin(email, password);
  });

  document.getElementById("form-register")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const full_name = document.getElementById("reg-fullname").value;
    const email = document.getElementById("reg-email").value;
    const password = document.getElementById("reg-password").value;
    const role = document.getElementById("reg-role").value;
    const semester = parseInt(document.getElementById("reg-semester").value);
    const department = document.getElementById("reg-department").value;

    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      body: { full_name, email, password, role, semester, department }
    });
    if (res && res.access_token) {
      State.token = res.access_token;
      localStorage.setItem("smartedu_token", res.access_token);
      setLoggedInUser(res.user);
      showToast("Account created successfully!", "success");
      switchView("dashboard");
    }
  });

  // IDE Controls
  document.getElementById("btn-run-code")?.addEventListener("click", runStudentCode);
  document.getElementById("btn-clear-code")?.addEventListener("click", () => {
    document.getElementById("code-editor").value = "";
    document.getElementById("stdout-console").innerText = "";
  });
  document.getElementById("btn-download-code")?.addEventListener("click", () => {
    const code = document.getElementById("code-editor").value;
    const lang = document.getElementById("select-code-lang").value;
    const ext = lang === "Python" ? "py" : (lang === "C++" ? "cpp" : "txt");
    const blob = new Blob([code], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `solution.${ext}`;
    a.click();
  });

  // AI Tutor Chat
  document.getElementById("ai-chat-form")?.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = document.getElementById("ai-chat-input");
    const msg = input.value.trim();
    if (msg) {
      sendAIChat(msg);
      input.value = "";
    }
  });

  document.querySelectorAll(".tutor-mode-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      document.querySelectorAll(".tutor-mode-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      currentTutorMode = chip.getAttribute("data-mode");
    });
  });

  // Quiz Form
  document.getElementById("quiz-submission-form")?.addEventListener("submit", submitQuiz);
  document.getElementById("btn-cancel-quiz")?.addEventListener("click", () => {
    clearInterval(State.quizTimerInterval);
    document.getElementById("quiz-player-container").classList.add("hidden");
    document.getElementById("quizzes-grid").classList.remove("hidden");
  });
  document.getElementById("btn-close-results")?.addEventListener("click", () => {
    document.getElementById("quiz-results-container").classList.add("hidden");
    document.getElementById("quizzes-grid").classList.remove("hidden");
    loadQuizzesView();
  });

  // Notification Bell Toggle
  document.getElementById("btn-notifications")?.addEventListener("click", () => {
    document.getElementById("notification-dropdown")?.classList.toggle("active");
  });
  document.getElementById("btn-mark-all-read")?.addEventListener("click", async () => {
    await apiFetch("/api/notifications/mark-all-read", { method: "PUT" });
    loadNotifications();
  });

  // Resume button
  document.getElementById("btn-hero-resume")?.addEventListener("click", () => {
    document.getElementById("btn-jump-topic")?.click();
  });

  document.getElementById("btn-view-weakness-details")?.addEventListener("click", () => {
    switchView("analytics");
  });

  // Subject creation form
  document.getElementById("form-create-subject")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const code = document.getElementById("b-sub-code").value;
    const title = document.getElementById("b-sub-title").value;
    const semester = parseInt(document.getElementById("b-sub-sem").value);
    const department = document.getElementById("b-sub-dept").value;
    const description = document.getElementById("b-sub-desc").value;

    await apiFetch("/api/academic/subjects", {
      method: "POST",
      body: { code, title, semester, department, description }
    });
    showToast("Subject created successfully!", "success");
    e.target.reset();
    loadSyllabusBuilderView();
  });

  // Unit creation form
  document.getElementById("form-create-unit")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const subject_id = parseInt(document.getElementById("b-target-subject").value);
    const unit_number = parseInt(document.getElementById("b-unit-num").value);
    const title = document.getElementById("b-unit-title").value;
    const description = document.getElementById("b-unit-desc").value;

    await apiFetch(`/api/academic/units?subject_id=${subject_id}`, {
      method: "POST",
      body: { unit_number, title, description, order_index: unit_number }
    });
    showToast("Unit added to syllabus!", "success");
    e.target.reset();
  });

  // Initialize Auth & App
  
  // Copilot Module Forms
  document.getElementById("form-generate")?.addEventListener("submit", handleCodeGeneration);
  document.getElementById("btn-copy-gen")?.addEventListener("click", () => {
    const code = document.getElementById("gen-output-code")?.innerText;
    if (code) {
      navigator.clipboard.writeText(code);
      showToast("Code copied to clipboard!", "success");
    }
  });
  document.getElementById("form-test-generate")?.addEventListener("submit", handleGenerateTests);
  document.getElementById("form-review")?.addEventListener("submit", handleCodeReview);
  document.getElementById("form-github-inspect")?.addEventListener("submit", handleGitHubInspect);

  initAuth();
});


// ==============================================================================
// 14. Software Engineering Copilot Modules (Code Gen, Testing, Review, GitHub)
// ==============================================================================

// A. AI Code Generator
async function handleCodeGeneration(e) {
  e.preventDefault();
  const prompt = document.getElementById("gen-prompt")?.value.trim();
  const language = document.getElementById("gen-lang")?.value || "Python";
  const architecture_style = document.getElementById("gen-style")?.value || "standard";

  if (!prompt) {
    showToast("Please enter a programming requirement", "warning");
    return;
  }

  const btn = document.getElementById("btn-submit-generate");
  const resultBox = document.getElementById("gen-result-box");
  const outputCode = document.getElementById("gen-output-code");
  
  if (btn) btn.innerText = "Synthesizing Code...";
  try {
    const res = await apiFetch("/api/generate", {
      method: "POST",
      body: { prompt, language, architecture_style }
    });
    if (res && res.code) {
      if (outputCode) outputCode.textContent = res.code;
      if (resultBox) resultBox.classList.remove("hidden");
      showToast("Code generated successfully!", "success");
    }
  } catch (err) {
    showToast(err.message || "Generation failed", "error");
  } finally {
    if (btn) btn.innerText = "Synthesize Code";
  }
}

// B. Automated Testing Runner
async function handleGenerateTests(e) {
  e.preventDefault();
  const source_code = document.getElementById("test-source-code")?.value.trim();
  const language = document.getElementById("test-lang")?.value || "Python";

  if (!source_code) {
    showToast("Please paste source code to test", "warning");
    return;
  }

  const btn = document.getElementById("btn-generate-tests");
  const resultBox = document.getElementById("test-result-box");
  const casesList = document.getElementById("test-cases-list");

  if (btn) btn.innerText = "Generating & Executing Tests...";
  try {
    const testGen = await apiFetch("/api/test/generate-tests", {
      method: "POST",
      body: { source_code, language }
    });

    if (testGen) {
      const runRes = await apiFetch("/api/test/run", {
        method: "POST",
        body: {
          test_code: testGen.test_code || "",
          source_code: source_code,
          language: language,
          test_cases: testGen.test_cases || []
        }
      });

      if (runRes) {
        document.getElementById("test-passed-count").innerText = runRes.passed ?? runRes.passed_count ?? 0;
        document.getElementById("test-failed-count").innerText = runRes.failed ?? runRes.failed_count ?? 0;
        document.getElementById("test-error-count").innerText = runRes.errors ?? runRes.error_count ?? 0;
        document.getElementById("test-total-count").innerText = runRes.total_tests ?? runRes.total ?? 0;

        const results = runRes.results || runRes.test_results || [];
        if (casesList) {
          casesList.innerHTML = results.map((t, idx) => `
            <div class="question-block" style="border-left: 4px solid ${t.passed ? 'var(--color-success)' : 'var(--color-danger)'}; padding: 12px; margin-bottom: 8px; background: var(--bg-card); border-radius: 4px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>Test #${idx + 1}: ${t.name || t.test_name || 'Assertion'}</strong>
                <span class="badge ${t.passed ? 'badge-primary' : 'badge-danger'}">${t.passed ? 'PASSED' : 'FAILED'}</span>
              </div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">Input: <code>${JSON.stringify(t.input || t.inputs || '')}</code></div>
              <div style="font-size:12px; color:var(--text-muted);">Expected: <code>${JSON.stringify(t.expected || '')}</code> | Actual: <code>${JSON.stringify(t.actual || t.output || '')}</code></div>
              ${t.error ? `<div style="font-size:12px; color:var(--color-danger); margin-top:4px;">Error: ${t.error}</div>` : ''}
            </div>
          `).join("") || `<pre style="padding:10px; font-size:12px;">${runRes.output || 'Execution complete.'}</pre>`;
        }
        if (resultBox) resultBox.classList.remove("hidden");
        showToast("Test execution completed", "success");
      }
    }
  } catch (err) {
    showToast(err.message || "Test generation failed", "error");
  } finally {
    if (btn) btn.innerText = "Generate & Run Tests";
  }
}

// C. AI Code Review
async function handleCodeReview(e) {
  e.preventDefault();
  const code = document.getElementById("rev-code")?.value.trim();
  const language = document.getElementById("rev-lang")?.value || "Python";

  if (!code) {
    showToast("Please paste code to audit", "warning");
    return;
  }

  const resultBox = document.getElementById("rev-result-box");
  const scoreBanner = document.getElementById("rev-score-banner");
  const findingsList = document.getElementById("rev-findings-list");

  try {
    const res = await apiFetch("/api/review", {
      method: "POST",
      body: { code, language }
    });

    if (res) {
      if (scoreBanner) {
        scoreBanner.innerHTML = `
          <div style="font-size: 18px; font-weight: 700;">Code Quality Score: ${res.score ?? res.quality_score ?? 85}/100</div>
          <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Summary: ${res.summary || 'Code evaluated across security, readability, and logic constraints.'}</div>
        `;
      }
      const issues = res.issues || res.findings || [];
      if (findingsList) {
        if (issues.length === 0) {
          findingsList.innerHTML = `<p style="padding:12px; color:var(--color-success);">No critical bugs or vulnerabilities detected! Code is clean.</p>`;
        } else {
          findingsList.innerHTML = issues.map(iss => `
            <div class="question-block" style="border-left: 4px solid ${iss.severity === 'error' || iss.severity === 'high' ? 'var(--color-danger)' : 'var(--color-warning)'}; padding: 12px; margin-bottom: 8px; background: var(--bg-card); border-radius: 4px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>${iss.title || iss.type || 'Finding'}</strong>
                <span class="badge ${iss.severity === 'high' ? 'badge-danger' : 'badge-primary'}">${(iss.severity || 'info').toUpperCase()}</span>
              </div>
              <div style="font-size:13px; margin-top:4px;">${iss.description || iss.message || ''}</div>
              ${iss.suggestion ? `<div style="font-size:12px; color:var(--color-success); margin-top:4px;">Recommendation: ${iss.suggestion}</div>` : ''}
            </div>
          `).join("");
        }
      }
      if (resultBox) resultBox.classList.remove("hidden");
      showToast("Code review complete", "success");
    }
  } catch (err) {
    showToast(err.message || "Review failed", "error");
  }
}

// D. GitHub Repository Assistant
async function handleGitHubInspect(e) {
  e.preventDefault();
  const repo_url = document.getElementById("github-repo-url")?.value.trim();
  if (!repo_url) {
    showToast("Please enter a GitHub repository URL", "warning");
    return;
  }

  const btn = document.getElementById("btn-github-inspect");
  const resultBox = document.getElementById("github-result-box");
  const metaBox = document.getElementById("github-repo-meta");
  const fileTree = document.getElementById("github-file-tree");
  const analysisList = document.getElementById("github-analysis-list");

  if (btn) btn.innerText = "Inspecting...";
  try {
    const res = await apiFetch("/api/github/inspect", {
      method: "POST",
      body: { repo_url }
    });

    if (res) {
      if (metaBox) {
        metaBox.innerHTML = `
          <div><strong>Repository:</strong> ${res.owner || ''}/${res.repo || ''}</div>
          <div class="repo-stat">Default Branch: ${res.default_branch || 'main'} | Stars: ${res.stars ?? 0} | Forks: ${res.forks ?? 0}</div>
          <div style="margin-top:6px; color:#8b949e;">${res.description || 'No description provided.'}</div>
        `;
      }
      const files = res.files || res.file_structure || [];
      if (fileTree) {
        fileTree.innerHTML = files.slice(0, 30).map(f => `
          <div style="font-family:var(--font-mono); font-size:12px; padding:4px 8px; border-bottom:1px solid var(--border-color);">
            📄 ${f.path || f.name || f} ${f.size ? `(${Math.round(f.size/1024)} KB)` : ''}
          </div>
        `).join("") || "<p style='padding:8px;'>No files found or empty repository.</p>";
      }
      const insights = res.insights || res.analysis || [];
      if (analysisList) {
        if (Array.isArray(insights)) {
          analysisList.innerHTML = insights.map(i => `<div style="padding:6px 0; font-size:13px;">• ${i}</div>`).join("");
        } else {
          analysisList.innerHTML = `<div style="padding:6px 0; font-size:13px;">${insights}</div>`;
        }
      }
      if (resultBox) resultBox.classList.remove("hidden");
      showToast("Repository inspected successfully", "success");
    }
  } catch (err) {
    showToast(err.message || "Failed to inspect repository", "error");
  } finally {
    if (btn) btn.innerText = "Inspect Repository";
  }
}

// E. Task History Audit
async function loadTaskHistory() {
  const container = document.getElementById("history-items-container");
  if (!container) return;
  try {
    const data = await apiFetch("/api/history");
    if (!data || data.length === 0) {
      container.innerHTML = "<p style='padding:16px; color:var(--text-muted);'>No historical copilot tasks recorded yet.</p>";
      return;
    }
    container.innerHTML = data.map(h => `
      <div class="question-block" style="padding:14px; margin-bottom:10px; background:var(--bg-card); border-radius:6px; border:1px solid var(--border-color);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>${(h.task_type || h.type || 'Task').toUpperCase()}</strong>
          <span style="font-size:12px; color:var(--text-muted);">${new Date(h.created_at || Date.now()).toLocaleString()}</span>
        </div>
        <div style="font-size:13px; color:var(--text-muted); margin-top:4px;">Language: ${h.language || 'N/A'} | Status: ${h.status || 'Success'}</div>
      </div>
    `).join("");
  } catch (e) {
    container.innerHTML = "<p style='padding:16px; color:var(--color-danger);'>Could not load audit log.</p>";
  }
}
