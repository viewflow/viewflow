/* eslint-env browser */
import './vf-modal-trigger.scss';


const MIN_SCALE = 0.5;
const MAX_SCALE = 16;
const ZOOM_STEP = 1.1;
// Pointer travel (px) past which a press is treated as a pan, not a click.
const DRAG_THRESHOLD = 4;


export class VFModalTrigger extends HTMLElement {
  connectedCallback() {
    this._contentEl = this.querySelector('.vf-modal-trigger__content');
    this._buttonEl = this.querySelector('.vf-modal-trigger__button');
    this._imageEl = this._contentEl.querySelector('img');

    this.addEventListener('click', this.onCloseDialog);
    this._contentEl.addEventListener('keydown', this.onOpenDialog);
    this._contentEl.addEventListener('click', this.onOpenDialog);
    this._buttonEl.addEventListener('click', this.onCloseDialog);

    // Pan & zoom is only meaningful for the flow diagram image the modal
    // wraps (see issue #367 -- large complex flows are otherwise unreadable).
    if (this._imageEl) {
      this._resetTransform();
      this._contentEl.addEventListener('wheel', this.onWheel, {passive: false});
      this._contentEl.addEventListener('mousedown', this.onPanStart);
      this._contentEl.addEventListener('dblclick', this.onResetZoom);
      this._imageEl.addEventListener('dragstart', this.onPreventDrag);
      this._contentEl.addEventListener('touchstart', this.onTouchStart, {passive: false});
      this._contentEl.addEventListener('touchmove', this.onTouchMove, {passive: false});
      this._contentEl.addEventListener('touchend', this.onTouchEnd);
    }
  }

  disconnectedCallback() {
    this.removeEventListener('click', this.onCloseDialog);
    this._contentEl.removeEventListener('click', this.onOpenDialog);
    this._contentEl.removeEventListener('keydown', this.onOpenDialog);
    this._buttonEl.removeEventListener('click', this.onCloseDialog);

    if (this._imageEl) {
      this._contentEl.removeEventListener('wheel', this.onWheel);
      this._contentEl.removeEventListener('mousedown', this.onPanStart);
      this._contentEl.removeEventListener('dblclick', this.onResetZoom);
      this._imageEl.removeEventListener('dragstart', this.onPreventDrag);
      this._contentEl.removeEventListener('touchstart', this.onTouchStart);
      this._contentEl.removeEventListener('touchmove', this.onTouchMove);
      this._contentEl.removeEventListener('touchend', this.onTouchEnd);
      this._endPan();
    }
  }

  get _isOpen() {
    return this.classList.contains('vf-modal-trigger--open');
  }

  onOpenDialog = (event) => {
    if (!this._isOpen) {
      if (event.type == 'click' || event.keyCode == 13 || event.keyCode == 20) {
        this.classList.add('vf-modal-trigger--open');
      }
    } else if (event.keyCode == 27) {
      this._close();
    }
    event.stopPropagation();
  }

  onCloseDialog = (event) => {
    this._close();
    event.stopPropagation();
  }

  _close() {
    this.classList.remove('vf-modal-trigger--open');
    // Start fresh next time the diagram is opened.
    this._resetTransform();
  }

  // ----- pan & zoom -----

  _resetTransform() {
    this._scale = 1;
    this._translateX = 0;
    this._translateY = 0;
    this._applyTransform();
  }

  _applyTransform() {
    this._imageEl.style.transformOrigin = '0 0';
    this._imageEl.style.transform =
      `translate(${this._translateX}px, ${this._translateY}px) scale(${this._scale})`;
  }

  _zoomAt(clientX, clientY, factor) {
    const nextScale = Math.min(
      MAX_SCALE, Math.max(MIN_SCALE, this._scale * factor));
    if (nextScale === this._scale) {
      return;
    }

    // Keep the point under the cursor pinned. transform-origin is 0 0, so the
    // image's on-screen top-left already folds in the current translate; the
    // offset from it scales by nextScale/scale.
    const rect = this._imageEl.getBoundingClientRect();
    const ratio = nextScale / this._scale;
    this._translateX += (clientX - rect.left) * (1 - ratio);
    this._translateY += (clientY - rect.top) * (1 - ratio);
    this._scale = nextScale;
    this._applyTransform();
  }

  onWheel = (event) => {
    if (!this._isOpen) {
      return;
    }
    event.preventDefault();
    this._zoomAt(
      event.clientX, event.clientY,
      event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP);
  }

  onResetZoom = (event) => {
    if (!this._isOpen) {
      return;
    }
    event.preventDefault();
    this._resetTransform();
  }

  onPreventDrag = (event) => {
    // Suppress the browser's native image ghost-drag while panning.
    event.preventDefault();
  }

  onPanStart = (event) => {
    if (!this._isOpen || event.button !== 0) {
      return;
    }
    // Let the close button / BPMN export link handle their own clicks.
    if (event.target.closest('a, button, .vf-modal-trigger__button')) {
      return;
    }
    event.preventDefault();
    this._panMoved = false;
    this._panTravel = 0;
    this._lastX = event.clientX;
    this._lastY = event.clientY;
    this.classList.add('vf-modal-trigger--panning');
    document.addEventListener('mousemove', this.onPanMove);
    document.addEventListener('mouseup', this.onPanEnd);
  }

  onPanMove = (event) => {
    const dx = event.clientX - this._lastX;
    const dy = event.clientY - this._lastY;
    this._lastX = event.clientX;
    this._lastY = event.clientY;
    this._panTravel += Math.abs(dx) + Math.abs(dy);
    if (this._panTravel > DRAG_THRESHOLD) {
      this._panMoved = true;
    }
    this._translateX += dx;
    this._translateY += dy;
    this._applyTransform();
  }

  onPanEnd = () => {
    this._endPan();
  }

  _endPan() {
    document.removeEventListener('mousemove', this.onPanMove);
    document.removeEventListener('mouseup', this.onPanEnd);
    this.classList.remove('vf-modal-trigger--panning');
    if (this._panMoved) {
      // A drag that ends over the backdrop would otherwise synthesize a click
      // that closes the dialog. Swallow that one click; drop the guard on the
      // next tick in case the drag produced no click at all.
      window.addEventListener('click', this._swallowClick, true);
      setTimeout(
        () => window.removeEventListener('click', this._swallowClick, true), 0);
    }
    this._panMoved = false;
  }

  _swallowClick = (event) => {
    event.stopPropagation();
    window.removeEventListener('click', this._swallowClick, true);
  }

  // ----- touch (one finger pans, two fingers pinch-zoom) -----

  onTouchStart = (event) => {
    if (!this._isOpen) {
      return;
    }
    if (event.touches.length === 1) {
      this._touchMode = 'pan';
      this._lastX = event.touches[0].clientX;
      this._lastY = event.touches[0].clientY;
    } else if (event.touches.length === 2) {
      this._touchMode = 'pinch';
      this._pinchDist = this._touchDistance(event.touches);
    }
  }

  onTouchMove = (event) => {
    if (!this._isOpen) {
      return;
    }
    if (this._touchMode === 'pan' && event.touches.length === 1) {
      event.preventDefault();
      const touch = event.touches[0];
      this._translateX += touch.clientX - this._lastX;
      this._translateY += touch.clientY - this._lastY;
      this._lastX = touch.clientX;
      this._lastY = touch.clientY;
      this._applyTransform();
    } else if (this._touchMode === 'pinch' && event.touches.length === 2) {
      event.preventDefault();
      const dist = this._touchDistance(event.touches);
      if (this._pinchDist > 0) {
        const mid = this._touchMidpoint(event.touches);
        this._zoomAt(mid.x, mid.y, dist / this._pinchDist);
      }
      this._pinchDist = dist;
    }
  }

  onTouchEnd = (event) => {
    if (event.touches.length === 0) {
      this._touchMode = null;
    } else if (event.touches.length === 1) {
      // Fall back from pinch to pan on the remaining finger.
      this._touchMode = 'pan';
      this._lastX = event.touches[0].clientX;
      this._lastY = event.touches[0].clientY;
    }
  }

  _touchDistance(touches) {
    return Math.hypot(
      touches[0].clientX - touches[1].clientX,
      touches[0].clientY - touches[1].clientY);
  }

  _touchMidpoint(touches) {
    return {
      x: (touches[0].clientX + touches[1].clientX) / 2,
      y: (touches[0].clientY + touches[1].clientY) / 2,
    };
  }
}
