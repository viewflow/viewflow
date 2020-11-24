/* eslint-env browser, node */
import Turbolinks from 'turbolinks';
import './index.scss';
import smartcrop from 'smartcrop';


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

  onChangeAvatarClick = (event) => {
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
    return smartcrop.crop(image, options).then((result) => {
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

  _upload(canvas) {
    this._uploadButtonEl.classList.toggle('vf-page-profile__avatar-change--disabled');

    const xhr = new XMLHttpRequest();
    xhr.open('POST', window.location.search, true);
    xhr.setRequestHeader('Turbolinks-Referrer', window.location);

    xhr.onload = (event) => {
      const Snapshot = Turbolinks.controller.view.getSnapshot().constructor;
      const Location = Turbolinks.controller.view.getSnapshot().getRootLocation().constructor;

      let location = xhr.getResponseHeader('turbolinks-location');
      const snapshot = Snapshot.wrap(xhr.response);

      if (!location) {
        location = window.location.href;
      }

      Turbolinks.controller.adapter.hideProgressBar();
      Turbolinks.controller.cache.put(new Location(location), snapshot);
      Turbolinks.visit(location, {action: 'restore'});
      Turbolinks.clearCache();

      if (xhr.status > 299) {
        Turbolinks.controller.disable();
      }
    };

    xhr.onerror = (event) => {
      Turbolinks.controller.adapter.hideProgressBar();
      this.uploadButton_.classList.toggle('vf-profile-avatar__change--disabled');
      this.showError('Request error');
    };

    Turbolinks.controller.adapter.showProgressBarAfterDelay();

    canvas.toBlob((blob) => {
      const formData = new FormData(this._formEl);
      formData.append('avatar', blob, 'avatar.jpg');
      xhr.send(formData);
    });
  }

  _showError(message, timeout=2000) {
    const snackbarEvent = new CustomEvent('vf-snackbar:show', {
      'detail': {message: message, timeout: timeout},
    });
    window.dispatchEvent(snackbarEvent);
  }
}
