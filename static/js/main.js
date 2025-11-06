// Flado - Main JavaScript

document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
});

function initializeApp() {
  setupTaskForm();
  setupTaskInteractions();
  setupSearch();
  setupDragAndDrop();
  setupKeyboardShortcuts();
}

// CSRF Protection Helpers
function getCSRFToken() {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  return metaTag ? metaTag.getAttribute('content') : '';
}

async function apiRequest(url, options = {}) {
  const token = getCSRFToken();
  const headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': token,
    ...options.headers
  };
  
  return fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin'
  });
}

function setupTaskForm() {
  const form = document.getElementById("task-form");
  const titleInput = document.getElementById("task-title-input");
  const descriptionInput = document.getElementById("task-description-input");
  const dueDateInput = document.getElementById("task-due-date-input");
  const detailsToggle = document.getElementById("task-details-toggle");
  const detailsForm = document.getElementById("task-details-form");
  const cancelDetails = document.getElementById("cancel-details");

  if (!form) return;

  if (titleInput && sessionStorage.getItem("focusTaskInput") === "true") {
    titleInput.focus();
    sessionStorage.removeItem("focusTaskInput");
  }

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const title = titleInput.value.trim();
    if (!title) return;

    const description = descriptionInput.value.trim() || null;
    const dueDate = dueDateInput.value || null;

    try {
      const response = await apiRequest("/api/tasks", {
        method: "POST",
        body: JSON.stringify({
          title,
          description,
          due_date: dueDate,
          tags: [],
        }),
      });

      if (response.ok) {
        const task = await response.json();
        sessionStorage.setItem("focusTaskInput", "true");
        location.reload();
      } else {
        const error = await response.json();
        alert("Error: " + (error.error || "Failed to create task"));
      }
    } catch (error) {
      console.error("Error creating task:", error);
      alert("Failed to create task. Please try again.");
    }

    titleInput.value = "";
    descriptionInput.value = "";
    dueDateInput.value = "";
    detailsForm.style.display = "none";
    detailsToggle.style.display = "none";
    if (titleInput) {
      titleInput.focus();
    }
  });

  titleInput.addEventListener("input", function () {
    if (this.value.trim() && detailsForm.style.display === "none") {
      detailsToggle.style.display = "block";
    }
  });

  if (detailsToggle) {
    detailsToggle.addEventListener("click", function () {
      detailsForm.style.display =
        detailsForm.style.display === "none" ? "block" : "none";
    });
  }

  if (cancelDetails) {
    cancelDetails.addEventListener("click", function () {
      descriptionInput.value = "";
      dueDateInput.value = "";
      detailsForm.style.display = "none";
    });
  }
}

function setupTaskInteractions() {
  document.addEventListener("change", async function (e) {
    if (e.target && e.target.classList && e.target.classList.contains("task-check")) {
      const taskId = parseInt(e.target.dataset.taskId);
      const completed = e.target.checked;

      try {
        const response = await apiRequest(`/api/tasks/${taskId}`, {
          method: "PATCH",
          body: JSON.stringify({ completed }),
        });

        if (response.ok) {
          const task = await response.json();
          const taskItem = e.target.closest(".task-item");
          if (completed) {
            taskItem.classList.add("completed");
          } else {
            taskItem.classList.remove("completed");
          }
        } else {
          e.target.checked = !completed;
          alert("Failed to update task");
        }
      } catch (error) {
        console.error("Error updating task:", error);
        e.target.checked = !completed;
        alert("Failed to update task. Please try again.");
      }
    }
  });

  document.addEventListener("dblclick", function (e) {
    if (e.target && e.target.classList && e.target.classList.contains("task-title")) {
      e.target.removeAttribute("readonly");
      e.target.focus();
      e.target.select();
    }
  });

  document.addEventListener(
    "blur",
    async function (e) {
      if (
        e.target &&
        e.target.classList &&
        e.target.classList.contains("task-title") &&
        !e.target.hasAttribute("readonly")
      ) {
        const taskId = parseInt(e.target.dataset.taskId);
        const title = e.target.value.trim();

        if (!title) {
          e.target.value = e.target.defaultValue;
          e.target.setAttribute("readonly", "");
          return;
        }

        try {
          const response = await apiRequest(`/api/tasks/${taskId}`, {
            method: "PATCH",
            body: JSON.stringify({ title }),
          });

          if (response.ok) {
            e.target.setAttribute("readonly", "");
          } else {
            alert("Failed to update task");
            e.target.value = e.target.defaultValue;
          }
        } catch (error) {
          console.error("Error updating task:", error);
          alert("Failed to update task. Please try again.");
          e.target.value = e.target.defaultValue;
        }

        e.target.setAttribute("readonly", "");
      }
    },
    true,
  );

  document.addEventListener("click", function (e) {
    if (e.target && e.target.classList && e.target.classList.contains("task-edit")) {
      const taskId = parseInt(e.target.dataset.taskId);
      openEditModal(taskId);
    }
  });

  document.addEventListener("click", function (e) {
    if (e.target && e.target.classList && e.target.classList.contains("task-delete")) {
      const taskId = parseInt(e.target.dataset.taskId);
      openDeleteModal(taskId, e.target.closest(".task-item"));
    }
  });
}

async function openEditModal(taskId) {
  try {
    const response = await apiRequest(`/api/tasks/${taskId}`, {
      method: "GET",
    });
    if (!response.ok) {
      alert("Failed to load task");
      return;
    }

    const task = await response.json();
    const modal = document.getElementById("edit-modal");
    const form = document.getElementById("edit-task-form");

    document.getElementById("edit-task-id").value = task.id;
    document.getElementById("edit-task-title").value = task.title;
    document.getElementById("edit-task-description").value =
      task.description || "";
    document.getElementById("edit-task-due-date").value = task.due_date || "";

    modal.style.display = "flex";

    form.onsubmit = async function (e) {
      e.preventDefault();

      const title = document.getElementById("edit-task-title").value.trim();
      if (!title) {
        alert("Title is required");
        return;
      }

      const description =
        document.getElementById("edit-task-description").value.trim() || null;
      const dueDate =
        document.getElementById("edit-task-due-date").value || null;

      try {
        const updateResponse = await apiRequest(`/api/tasks/${taskId}`, {
          method: "PATCH",
          body: JSON.stringify({
            title,
            description,
            due_date: dueDate,
          }),
        });

        if (updateResponse.ok) {
          modal.style.display = "none";
          location.reload();
        } else {
          const error = await updateResponse.json();
          alert("Error: " + (error.error || "Failed to update task"));
        }
      } catch (error) {
        console.error("Error updating task:", error);
        alert("Failed to update task. Please try again.");
      }
    };

    document.getElementById("cancel-edit").onclick = function () {
      modal.style.display = "none";
    };

    document.getElementById("modal-close").onclick = function () {
      modal.style.display = "none";
    };

    modal.onclick = function (e) {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    };
  } catch (error) {
    console.error("Error opening edit modal:", error);
    alert("Failed to load task");
  }
}

function openDeleteModal(taskId, taskElement) {
  const modal = document.getElementById("delete-modal");
  const cancelButton = document.getElementById("delete-cancel");
  const confirmButton = document.getElementById("delete-confirm");
  let isConfirming = false;

  modal.style.display = "flex";

  const closeModal = function () {
    modal.style.display = "none";
    modal.onclick = null;
    cancelButton.onclick = null;
    confirmButton.onclick = null;
    document.removeEventListener("keydown", handleKeydown);
    isConfirming = false;
  };

  cancelButton.onclick = closeModal;

  modal.onclick = function (e) {
    if (e.target === modal) {
      closeModal();
    }
  };

  confirmButton.onclick = async function () {
    if (isConfirming) return;
    isConfirming = true;
    try {
      const response = await apiRequest(`/api/tasks/${taskId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        taskElement.remove();
        closeModal();

        const taskList = document.getElementById("task-list");
        if (taskList && taskList.children.length === 0) {
          location.reload();
        }
      } else {
        alert("Failed to delete task");
      }
    } catch (error) {
      console.error("Error deleting task:", error);
      alert("Failed to delete task. Please try again.");
    } finally {
      isConfirming = false;
    }
  };

  const handleKeydown = function (e) {
    if (e.key === "Escape") {
      closeModal();
    } else if (e.key === "Enter") {
      e.preventDefault();
      confirmButton.click();
    }
  };
  confirmButton.focus();
  document.addEventListener("keydown", handleKeydown);
}

function setupSearch() {
  const searchInput = document.getElementById("search-input");
  const searchClear = document.getElementById("search-clear");
  const container = document.querySelector(".tasks-container");
  let searchTimeout = null;

  if (!searchInput) return;

  if (searchInput.value && searchClear) {
    searchClear.style.display = "block";
  }

  const performSearch = async (query) => {
    const url = new URL(window.location);
    if (query) {
      url.searchParams.set("search", query);
    } else {
      url.searchParams.delete("search");
    }

    try {
      const response = await fetch(url, {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch search results");
      }

      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newTaskList = doc.querySelector("#task-list");
      const newContainer = doc.querySelector(".tasks-container");
      const taskList = document.getElementById("task-list");

      if (taskList && newTaskList) {
        taskList.innerHTML = newTaskList.innerHTML;
      }

      if (container && newContainer) {
        container.dataset.filter = newContainer.dataset.filter || "all";
        container.dataset.search = newContainer.dataset.search || "";
      }

      window.history.replaceState({}, "", url);
    } catch (error) {
      console.error("Error performing search:", error);
      window.location.href = url.toString();
    }
  };

  searchInput.addEventListener("input", function () {
    const query = this.value.trim();

    if (searchClear) {
      searchClear.style.display = query ? "block" : "none";
    }

    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    searchTimeout = setTimeout(() => performSearch(query), 300);
  });

  searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      const query = this.value.trim();
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      performSearch(query);
    }
  });

  if (searchClear) {
    searchClear.addEventListener("click", function () {
      searchInput.value = "";
      searchClear.style.display = "none";
      if (searchTimeout) {
        clearTimeout(searchTimeout);
      }
      performSearch("");
      searchInput.focus();
    });
  }
}

function setupDragAndDrop() {
  const container = document.querySelector(".tasks-container");
  if (!container) return;

  const taskList = document.getElementById("task-list");
  if (!taskList) return;
  if (taskList.dataset.dragSetup === "true") return;

  const isReorderEnabled = () => {
    const filterType = container.dataset.filter || "all";
    const hasSearchQuery = (container.dataset.search || "").trim().length > 0;
    return filterType === "all" && !hasSearchQuery;
  };

  let draggedElement = null;

  taskList.addEventListener("dragstart", function (e) {
    if (!isReorderEnabled()) {
      e.preventDefault();
      return;
    }
    if (e.target && e.target.classList && e.target.classList.contains("task-item")) {
      draggedElement = e.target;
      e.target.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
    }
  });

  taskList.addEventListener("dragend", function (e) {
    if (e.target && e.target.classList && e.target.classList.contains("task-item")) {
      e.target.classList.remove("dragging");
    }
  });

  taskList.addEventListener("dragover", function (e) {
    if (!isReorderEnabled()) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    e.dataTransfer.dropEffect = "move";

    const afterElement = getDragAfterElement(taskList, e.clientY);
    const dragging = document.querySelector(".dragging");

    if (afterElement == null) {
      taskList.appendChild(dragging);
    } else {
      taskList.insertBefore(dragging, afterElement);
    }
  });

  taskList.addEventListener("drop", async function (e) {
    if (!isReorderEnabled()) {
      e.preventDefault();
      return;
    }

    e.preventDefault();
    const taskItems = Array.from(taskList.querySelectorAll(".task-item"));
    const taskIds = taskItems.map((item) => parseInt(item.dataset.taskId));

    try {
      const response = await apiRequest("/api/tasks/reorder", {
        method: "POST",
        body: JSON.stringify({ task_ids: taskIds }),
      });

      if (!response.ok) {
        alert("Failed to reorder tasks");
        location.reload();
      }
    } catch (error) {
      console.error("Error reordering tasks:", error);
      alert("Failed to reorder tasks. Please try again.");
      location.reload();
    }
  });

  taskList.dataset.dragSetup = "true";
}

function getDragAfterElement(container, y) {
  const draggableElements = [
    ...container.querySelectorAll(".task-item:not(.dragging)"),
  ];

  return draggableElements.reduce(
    (closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;

      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    },
    { offset: Number.NEGATIVE_INFINITY },
  ).element;
}

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      const searchInput = document.getElementById("search-input");
      if (searchInput) {
        searchInput.focus();
      }
    }

    if ((e.ctrlKey || e.metaKey) && e.key === "n") {
      e.preventDefault();
      const taskInput = document.getElementById("task-title-input");
      if (taskInput) {
        taskInput.focus();
      }
    }
  });
}
