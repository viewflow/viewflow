/* eslint-env browser, node */
import './index.scss';


export class VPageProfileAvatar extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this._formEl = this.querySelector('form');
      this._uploadButtonEl = this.querySelector('.vf-page-profile__avatar-change');
      this._uploadButtonEl.addEventListener('change', this.onChangeAvatarClick);
    });
  }

  disconnectedCallback() {
    this._uploadButtonEl.removeEventListener('change', this.onChangeAvatarClick);
  }

  onChangeAvatarClick = async (event) => {
    this._uploadButtonEl.classList.toggle('vf-page-profile__avatar-change--disabled');

    const files = event.target.files;
    if (files.length === 0 || files[0].type.indexOf('image') === -1) {
      this.showError('No images selected');
    }

    const reader = new FileReader();
    reader.onload = (readerEvent) => {
      const image = new Image();
      image.onload = () => {
        this._crop(image).then((cropCanvas) => {
          this._upload(cropCanvas);
        }).catch((error) => {
          this._showError(error.message || 'Image cropping error');
        });
      };
      image.src = readerEvent.target.result;
    };
    reader.readAsDataURL(files[0]);
  };

  _crop(image, onSuccess) {
    const options = {
      minScale: 1,
      width: 256,
      height: 256,
    };
    return window.smartcrop.crop(image, options).then((result) => {
      const cropCanvas = document.createElement('canvas');
      cropCanvas.width = 256;
      cropCanvas.height = 256;
      cropCanvas.getContext('2d').drawImage(
          image,
          result.topCrop.x, result.topCrop.y, result.topCrop.width, result.topCrop.height,
          0, 0, 256, 256,
      );
      return cropCanvas;
    });
  }

  async _upload(canvas) {
    const blob = await new Promise((resolve) => canvas.toBlob(resolve));
    const file = new File([blob], 'avatar.jpg', {type: 'image/jpeg', lastModified: new Date().getTime()});
    const container = new DataTransfer();
    container.items.add(file);

    this._formEl.querySelector('input[type=file]').files = container.files;
    this._formEl.querySelector('button').click();
  }

  _showError(message, timeout=2000) {
    const snackbarEvent = new CustomEvent('vf-snackbar:show', {
      'detail': {message: message, timeout: timeout},
    });
    window.dispatchEvent(snackbarEvent);
  }
}
