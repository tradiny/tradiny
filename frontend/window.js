/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

export class PopupWindow {
  constructor(targetElementId, width = "auto", closeDisabled = false) {
    this.targetElement = document.getElementById(targetElementId);
    this.width = width; // Accept width as a parameter
    this.closeDisabled = closeDisabled;
    this.popupElement = null;
    this.backdrop = null;
    this.contentContainer = null; // Separate container for the content
    this.closeEvents = [];
    this.createPopup();
  }

  createPopup() {
    // Create the backdrop
    this.backdrop = document.createElement("div");
    this.backdrop.style.position = "absolute";
    this.backdrop.style.top = "0";
    this.backdrop.style.left = "0";
    this.backdrop.style.width = "100%";
    this.backdrop.style.height = "100%";
    this.backdrop.style.zIndex = "1";
    this.backdrop.classList.add("backdrop-show"); // Add class for show animation
    if (!this.closeDisabled) {
      this.backdrop.addEventListener("click", () => this.closePopup());
    }

    // Create the popup window element
    this.popupElement = document.createElement("div");
    this.popupElement.style.position = "absolute";
    this.popupElement.style.left = "50%";
    this.popupElement.style.top = "5%";
    this.popupElement.style.transform = "translate(-50%, 0%)";
    this.popupElement.style.maxWidth = "100%";
    // this.popupElement.style.width = this.width;
    // this.popupElement.style.padding = '15px 10px 10px 10px';
    this.popupElement.style.zIndex = "2";
    this.popupElement.style.overflowY = "auto";
    this.popupElement.style.maxHeight = "80%";
    // this.popupElement.style.border = '1px solid #ccc';
    this.popupElement.classList.add("popup-show"); // Add class for show animation

    // Create the close button

    let closeButton;
    if (!this.closeDisabled) {
      closeButton = document.createElement("button");
      closeButton.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8" fill="currentColor" class="bi bi-x-lg" viewBox="0 0 16 16">
            <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z"/>
            </svg>`;
      closeButton.style.position = "absolute";
      closeButton.style.top = "5px";
      closeButton.style.right = "5px";
      closeButton.style.height = "16px";
      closeButton.style.width = "16px";
      closeButton.style.padding = "0";
      closeButton.style.border = "none";
      closeButton.style.background = "none";
      closeButton.style.cursor = "pointer";
      closeButton.style.color = "inherit";
      closeButton.addEventListener("click", (e) => {
        e.stopPropagation(); // Prevent the backdrop click event
        this.closePopup();
      });
    }

    // Create the content container
    this.contentContainer = document.createElement("div");
    this.popupElement.appendChild(this.contentContainer);

    if (!this.closeDisabled) {
      this.popupElement.appendChild(closeButton);
    }
    this.targetElement.appendChild(this.backdrop);
    this.targetElement.appendChild(this.popupElement);

    function debounce(func, wait) {
      let timeout;
      return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
      };
    }
    this.debouncedAdjustPopup = debounce(this.adjustPopup.bind(this), 100); // Adjust the delay as needed

    this.resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        if (entry.target === this.popupElement) {
          this.debouncedAdjustPopup();
        }
      }
    });

    this.resizeObserver.observe(this.popupElement);

    if (!this.closeDisabled) {
      this.boundHandleKeyDown = this.handleKeyDown.bind(this);
      document.addEventListener("keydown", this.boundHandleKeyDown);
    }
  }

  handleKeyDown(event) {
    if (event.key === "Escape") {
      this.closePopup();
    } else if (event.key === "Enter") {
      this.clickLastButtonIfNotEditing();
    }
  }

  clickFirstButton() {
    const button = this.popupElement.querySelector('input[type="button"]');
    if (button) {
      button.click();
    }
  }
  clickLastButtonIfNotEditing() {
    const activeElement = document.activeElement;

    // Check if the active element is not a textarea or an input field
    if (
      activeElement.tagName !== "TEXTAREA" &&
      activeElement.tagName !== "INPUT"
    ) {
      const buttons = this.popupElement.querySelectorAll(
        'input[type="button"]',
      );
      if (buttons.length > 0) {
        buttons[buttons.length - 1].click();
      }
    }
  }

  render(content) {
    // Insert content into the content container
    this.contentContainer.innerHTML = content;
    this.adjustPopup();
  }

  adjustPopup() {
    // Adjust scrolling based on the height of the content
    const maxHeight = this.targetElement.clientHeight;
    if (this.popupElement.scrollHeight > maxHeight - 200) {
      this.popupElement.style.overflowY = "scroll";
    } else {
      this.popupElement.style.overflowY = "hidden";
    }
  }

  closePopup() {
    document.removeEventListener("keydown", this.boundHandleKeyDown);

    // Add hide animation classes
    this.popupElement.classList.remove("popup-show");
    this.popupElement.classList.add("popup-hide");
    this.backdrop.classList.remove("backdrop-show");
    this.backdrop.classList.add("backdrop-hide");

    // Remove the popup and the backdrop from the DOM after the animation ends
    setTimeout(() => {
      this.popupElement.remove();
      this.backdrop.remove();
    }, 50); // Match the duration of the hide animation
    this.closeEvents.forEach((callback) => {
      if (typeof callback === "function") {
        callback(); // Call the function
      }
    });
  }

  onClose(evt) {
    this.closeEvents.push(evt);
  }
}
