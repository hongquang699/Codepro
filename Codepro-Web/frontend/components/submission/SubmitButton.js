/**
 * SubmitButton Component
 * Manages submit button state with loader and Flaticon icon.
 */
const SubmitButton = {
  setLoading(buttonElement, isLoading = true, loadingText = 'Đang nộp...') {
    if (!buttonElement) return;
    if (isLoading) {
      buttonElement.disabled = true;
      buttonElement.dataset.origHtml = buttonElement.innerHTML;
      buttonElement.innerHTML = `<i class="fi fi-rr-spinner spin-icon"></i> ${loadingText}`;
    } else {
      buttonElement.disabled = false;
      if (buttonElement.dataset.origHtml) {
        buttonElement.innerHTML = buttonElement.dataset.origHtml;
      } else {
        buttonElement.innerHTML = `<i class="fi fi-rr-paper-plane"></i> Nộp bài`;
      }
    }
  }
};

if (typeof window !== 'undefined') {
  window.SubmitButton = SubmitButton;
}
