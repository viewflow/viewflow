/*
Turbolinks 5.3.0-beta.0
Copyright © 2019 Basecamp, LLC
 */
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    (global = global || self, global.Turbolinks = factory());
}(this, function () { 'use strict';

    /*! *****************************************************************************
    Copyright (c) Microsoft Corporation. All rights reserved.
    Licensed under the Apache License, Version 2.0 (the "License"); you may not use
    this file except in compliance with the License. You may obtain a copy of the
    License at http://www.apache.org/licenses/LICENSE-2.0

    THIS CODE IS PROVIDED ON AN *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
    WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
    MERCHANTABLITY OR NON-INFRINGEMENT.

    See the Apache Version 2.0 License for specific language governing permissions
    and limitations under the License.
    ***************************************************************************** */
    /* global Reflect, Promise */

    var extendStatics = function(d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };

    function __extends(d, b) {
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    }

    var __assign = function() {
        __assign = Object.assign || function __assign(t) {
            for (var s, i = 1, n = arguments.length; i < n; i++) {
                s = arguments[i];
                for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p)) t[p] = s[p];
            }
            return t;
        };
        return __assign.apply(this, arguments);
    };

    function __makeTemplateObject(cooked, raw) {
        if (Object.defineProperty) { Object.defineProperty(cooked, "raw", { value: raw }); } else { cooked.raw = raw; }
        return cooked;
    }

    var Location = (function () {
        function Location(url) {
            var linkWithAnchor = document.createElement("a");
            linkWithAnchor.href = url;
            this.absoluteURL = linkWithAnchor.href;
            var anchorLength = linkWithAnchor.hash.length;
            if (anchorLength < 2) {
                this.requestURL = this.absoluteURL;
            }
            else {
                this.requestURL = this.absoluteURL.slice(0, -anchorLength);
                this.anchor = linkWithAnchor.hash.slice(1);
            }
        }
        Object.defineProperty(Location, "currentLocation", {
            get: function () {
                return this.wrap(window.location.toString());
            },
            enumerable: true,
            configurable: true
        });
        Location.wrap = function (locatable) {
            if (typeof locatable == "string") {
                return new this(locatable);
            }
            else if (locatable != null) {
                return locatable;
            }
        };
        Location.prototype.getOrigin = function () {
            return this.absoluteURL.split("/", 3).join("/");
        };
        Location.prototype.getPath = function () {
            return (this.requestURL.match(/\/\/[^/]*(\/[^?;]*)/) || [])[1] || "/";
        };
        Location.prototype.getPathComponents = function () {
            return this.getPath().split("/").slice(1);
        };
        Location.prototype.getLastPathComponent = function () {
            return this.getPathComponents().slice(-1)[0];
        };
        Location.prototype.getExtension = function () {
            return (this.getLastPathComponent().match(/\.[^.]*$/) || [])[0] || "";
        };
        Location.prototype.isHTML = function () {
            return this.getExtension().match(/^(?:|\.(?:htm|html|xhtml))$/);
        };
        Location.prototype.isPrefixedBy = function (location) {
            var prefixURL = getPrefixURL(location);
            return this.isEqualTo(location) || stringStartsWith(this.absoluteURL, prefixURL);
        };
        Location.prototype.isEqualTo = function (location) {
            return location && this.absoluteURL === location.absoluteURL;
        };
        Location.prototype.toCacheKey = function () {
            return this.requestURL;
        };
        Location.prototype.toJSON = function () {
            return this.absoluteURL;
        };
        Location.prototype.toString = function () {
            return this.absoluteURL;
        };
        Location.prototype.valueOf = function () {
            return this.absoluteURL;
        };
        return Location;
    }());
    function getPrefixURL(location) {
        return addTrailingSlash(location.getOrigin() + location.getPath());
    }
    function addTrailingSlash(url) {
        return stringEndsWith(url, "/") ? url : url + "/";
    }
    function stringStartsWith(string, prefix) {
        return string.slice(0, prefix.length) === prefix;
    }
    function stringEndsWith(string, suffix) {
        return string.slice(-suffix.length) === suffix;
    }
    //# sourceMappingURL=location.js.map

    function array(values) {
        return Array.prototype.slice.call(values);
    }
    var closest = (function () {
        var html = document.documentElement;
        var match = html.matches
            || html.webkitMatchesSelector
            || html.msMatchesSelector
            || html.mozMatchesSelector;
        var closest = html.closest || function (selector) {
            var element = this;
            while (element) {
                if (match.call(element, selector)) {
                    return element;
                }
                else {
                    element = element.parentElement;
                }
            }
        };
        return function (element, selector) {
            return closest.call(element, selector);
        };
    })();
    function defer(callback) {
        setTimeout(callback, 1);
    }
    function dispatch(eventName, _a) {
        var _b = _a === void 0 ? {} : _a, target = _b.target, cancelable = _b.cancelable, data = _b.data;
        var event = document.createEvent("Events");
        event.initEvent(eventName, true, cancelable == true);
        event.data = data || {};
        if (event.cancelable && !preventDefaultSupported) {
            var preventDefault_1 = event.preventDefault;
            event.preventDefault = function () {
                if (!this.defaultPrevented) {
                    Object.defineProperty(this, "defaultPrevented", { get: function () { return true; } });
                }
                preventDefault_1.call(this);
            };
        }
        (target || document).dispatchEvent(event);
        return event;
    }
    var preventDefaultSupported = (function () {
        var event = document.createEvent("Events");
        event.initEvent("test", true, true);
        event.preventDefault();
        return event.defaultPrevented;
    })();
    function unindent(strings) {
        var values = [];
        for (var _i = 1; _i < arguments.length; _i++) {
            values[_i - 1] = arguments[_i];
        }
        var lines = trimLeft(interpolate(strings, values)).split("\n");
        var match = lines[0].match(/^\s+/);
        var indent = match ? match[0].length : 0;
        return lines.map(function (line) { return line.slice(indent); }).join("\n");
    }
    function trimLeft(string) {
        return string.replace(/^\n/, "");
    }
    function interpolate(strings, values) {
        return strings.reduce(function (result, string, i) {
            var value = values[i] == undefined ? "" : values[i];
            return result + string + value;
        }, "");
    }
    function uuid() {
        return Array.apply(null, { length: 36 }).map(function (_, i) {
            if (i == 8 || i == 13 || i == 18 || i == 23) {
                return "-";
            }
            else if (i == 14) {
                return "4";
            }
            else if (i == 19) {
                return (Math.floor(Math.random() * 4) + 8).toString(16);
            }
            else {
                return Math.floor(Math.random() * 15).toString(16);
            }
        }).join("");
    }
    //# sourceMappingURL=util.js.map

    var SystemStatusCode;
    (function (SystemStatusCode) {
        SystemStatusCode[SystemStatusCode["networkFailure"] = 0] = "networkFailure";
        SystemStatusCode[SystemStatusCode["timeoutFailure"] = -1] = "timeoutFailure";
        SystemStatusCode[SystemStatusCode["contentTypeMismatch"] = -2] = "contentTypeMismatch";
    })(SystemStatusCode || (SystemStatusCode = {}));
    var HttpRequest = (function () {
        function HttpRequest(delegate, location, referrer) {
            var _this = this;
            this.failed = false;
            this.progress = 0;
            this.sent = false;
            this.requestProgressed = function (event) {
                if (event.lengthComputable) {
                    _this.setProgress(event.loaded / event.total);
                }
            };
            this.requestLoaded = function () {
                _this.endRequest(function (xhr) {
                    var contentType = xhr.getResponseHeader("Content-Type");
                    if (contentTypeIsHTML(contentType)) {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            var redirectedToLocation = Location.wrap(xhr.getResponseHeader("Turbolinks-Location"));
                            _this.delegate.requestCompletedWithResponse(xhr.responseText, redirectedToLocation);
                        }
                        else {
                            _this.failed = true;
                            _this.delegate.requestFailedWithStatusCode(xhr.status, xhr.responseText);
                        }
                    }
                    else {
                        _this.failed = true;
                        _this.delegate.requestFailedWithStatusCode(SystemStatusCode.contentTypeMismatch);
                    }
                });
            };
            this.requestFailed = function () {
                _this.endRequest(function () {
                    _this.failed = true;
                    _this.delegate.requestFailedWithStatusCode(SystemStatusCode.networkFailure);
                });
            };
            this.requestTimedOut = function () {
                _this.endRequest(function () {
                    _this.failed = true;
                    _this.delegate.requestFailedWithStatusCode(SystemStatusCode.timeoutFailure);
                });
            };
            this.requestCanceled = function () {
                _this.endRequest();
            };
            this.delegate = delegate;
            this.location = location;
            this.referrer = referrer;
            this.location = Location.wrap(location);
            this.referrer = Location.wrap(referrer);
            this.url = location.absoluteURL;
            this.createXHR();
        }
        HttpRequest.prototype.send = function () {
            if (this.xhr && !this.sent) {
                this.notifyApplicationBeforeRequestStart();
                this.setProgress(0);
                this.xhr.send();
                this.sent = true;
                this.delegate.requestStarted();
            }
        };
        HttpRequest.prototype.cancel = function () {
            if (this.xhr && this.sent) {
                this.xhr.abort();
            }
        };
        HttpRequest.prototype.notifyApplicationBeforeRequestStart = function () {
            dispatch("turbolinks:request-start", { data: { url: this.url, xhr: this.xhr } });
        };
        HttpRequest.prototype.notifyApplicationAfterRequestEnd = function () {
            dispatch("turbolinks:request-end", { data: { url: this.url, xhr: this.xhr } });
        };
        HttpRequest.prototype.createXHR = function () {
            var xhr = this.xhr = new XMLHttpRequest;
            var referrer = this.referrer ? this.referrer.absoluteURL : "";
            var timeout = HttpRequest.timeout * 1000;
            xhr.open("GET", this.url, true);
            xhr.timeout = timeout;
            xhr.setRequestHeader("Accept", "text/html, application/xhtml+xml");
            xhr.setRequestHeader("Turbolinks-Referrer", referrer);
            xhr.onprogress = this.requestProgressed;
            xhr.onload = this.requestLoaded;
            xhr.onerror = this.requestFailed;
            xhr.ontimeout = this.requestTimedOut;
            xhr.onabort = this.requestCanceled;
        };
        HttpRequest.prototype.endRequest = function (callback) {
            if (callback === void 0) { callback = function () { }; }
            if (this.xhr) {
                this.notifyApplicationAfterRequestEnd();
                callback(this.xhr);
                this.destroy();
            }
        };
        HttpRequest.prototype.setProgress = function (progress) {
            this.progress = progress;
            this.delegate.requestProgressed(progress);
        };
        HttpRequest.prototype.destroy = function () {
            this.setProgress(1);
            this.delegate.requestFinished();
        };
        HttpRequest.timeout = 60;
        return HttpRequest;
    }());
    function contentTypeIsHTML(contentType) {
        return (contentType || "").match(/^text\/html|^application\/xhtml\+xml/);
    }
    //# sourceMappingURL=http_request.js.map

    var ProgressBar = (function () {
        function ProgressBar() {
            var _this = this;
            this.stylesheetElement = this.createStylesheetElement();
            this.progressElement = this.createProgressElement();
            this.hiding = false;
            this.value = 0;
            this.visible = false;
            this.trickle = function () {
                _this.setValue(_this.value + Math.random() / 100);
            };
        }
        Object.defineProperty(ProgressBar, "defaultCSS", {
            get: function () {
                return unindent(templateObject_1 || (templateObject_1 = __makeTemplateObject(["\n      .turbolinks-progress-bar {\n        position: fixed;\n        display: block;\n        top: 0;\n        left: 0;\n        height: 3px;\n        background: #0076ff;\n        z-index: 9999;\n        transition:\n          width ", "ms ease-out,\n          opacity ", "ms ", "ms ease-in;\n        transform: translate3d(0, 0, 0);\n      }\n    "], ["\n      .turbolinks-progress-bar {\n        position: fixed;\n        display: block;\n        top: 0;\n        left: 0;\n        height: 3px;\n        background: #0076ff;\n        z-index: 9999;\n        transition:\n          width ", "ms ease-out,\n          opacity ", "ms ", "ms ease-in;\n        transform: translate3d(0, 0, 0);\n      }\n    "])), ProgressBar.animationDuration, ProgressBar.animationDuration / 2, ProgressBar.animationDuration / 2);
            },
            enumerable: true,
            configurable: true
        });
        ProgressBar.prototype.show = function () {
            if (!this.visible) {
                this.visible = true;
                this.installStylesheetElement();
                this.installProgressElement();
                this.startTrickling();
            }
        };
        ProgressBar.prototype.hide = function () {
            var _this = this;
            if (this.visible && !this.hiding) {
                this.hiding = true;
                this.fadeProgressElement(function () {
                    _this.uninstallProgressElement();
                    _this.stopTrickling();
                    _this.visible = false;
                    _this.hiding = false;
                });
            }
        };
        ProgressBar.prototype.setValue = function (value) {
            this.value = value;
            this.refresh();
        };
        ProgressBar.prototype.installStylesheetElement = function () {
            document.head.insertBefore(this.stylesheetElement, document.head.firstChild);
        };
        ProgressBar.prototype.installProgressElement = function () {
            this.progressElement.style.width = "0";
            this.progressElement.style.opacity = "1";
            document.documentElement.insertBefore(this.progressElement, document.body);
            this.refresh();
        };
        ProgressBar.prototype.fadeProgressElement = function (callback) {
            this.progressElement.style.opacity = "0";
            setTimeout(callback, ProgressBar.animationDuration * 1.5);
        };
        ProgressBar.prototype.uninstallProgressElement = function () {
            if (this.progressElement.parentNode) {
                document.documentElement.removeChild(this.progressElement);
            }
        };
        ProgressBar.prototype.startTrickling = function () {
            if (!this.trickleInterval) {
                this.trickleInterval = window.setInterval(this.trickle, ProgressBar.animationDuration);
            }
        };
        ProgressBar.prototype.stopTrickling = function () {
            window.clearInterval(this.trickleInterval);
            delete this.trickleInterval;
        };
        ProgressBar.prototype.refresh = function () {
            var _this = this;
            requestAnimationFrame(function () {
                _this.progressElement.style.width = 10 + (_this.value * 90) + "%";
            });
        };
        ProgressBar.prototype.createStylesheetElement = function () {
            var element = document.createElement("style");
            element.type = "text/css";
            element.textContent = ProgressBar.defaultCSS;
            return element;
        };
        ProgressBar.prototype.createProgressElement = function () {
            var element = document.createElement("div");
            element.className = "turbolinks-progress-bar";
            return element;
        };
        ProgressBar.animationDuration = 300;
        return ProgressBar;
    }());
    var templateObject_1;
    //# sourceMappingURL=progress_bar.js.map

    var BrowserAdapter = (function () {
        function BrowserAdapter(controller) {
            var _this = this;
            this.progressBar = new ProgressBar;
            this.showProgressBar = function () {
                _this.progressBar.show();
            };
            this.controller = controller;
        }
        BrowserAdapter.prototype.visitProposedToLocationWithAction = function (location, action) {
            var restorationIdentifier = uuid();
            this.controller.startVisitToLocationWithAction(location, action, restorationIdentifier);
        };
        BrowserAdapter.prototype.visitStarted = function (visit) {
            visit.issueRequest();
            visit.changeHistory();
            visit.loadCachedSnapshot();
        };
        BrowserAdapter.prototype.visitRequestStarted = function (visit) {
            this.progressBar.setValue(0);
            if (visit.hasCachedSnapshot() || visit.action != "restore") {
                this.showProgressBarAfterDelay();
            }
            else {
                this.showProgressBar();
            }
        };
        BrowserAdapter.prototype.visitRequestProgressed = function (visit) {
            this.progressBar.setValue(visit.progress);
        };
        BrowserAdapter.prototype.visitRequestCompleted = function (visit) {
            visit.loadResponse();
        };
        BrowserAdapter.prototype.visitRequestFailedWithStatusCode = function (visit, statusCode) {
            switch (statusCode) {
                case SystemStatusCode.networkFailure:
                case SystemStatusCode.timeoutFailure:
                case SystemStatusCode.contentTypeMismatch:
                    return this.reload();
                default:
                    return visit.loadResponse();
            }
        };
        BrowserAdapter.prototype.visitRequestFinished = function (visit) {
            this.hideProgressBar();
        };
        BrowserAdapter.prototype.visitCompleted = function (visit) {
            visit.followRedirect();
        };
        BrowserAdapter.prototype.pageInvalidated = function () {
            this.reload();
        };
        BrowserAdapter.prototype.visitFailed = function (visit) {
        };
        BrowserAdapter.prototype.visitRendered = function (visit) {
        };
        BrowserAdapter.prototype.showProgressBarAfterDelay = function () {
            this.progressBarTimeout = window.setTimeout(this.showProgressBar, this.controller.progressBarDelay);
        };
        BrowserAdapter.prototype.hideProgressBar = function () {
            this.progressBar.hide();
            if (this.progressBarTimeout != null) {
                window.clearTimeout(this.progressBarTimeout);
                delete this.progressBarTimeout;
            }
        };
        BrowserAdapter.prototype.reload = function () {
            window.location.reload();
        };
        return BrowserAdapter;
    }());
    //# sourceMappingURL=browser_adapter.js.map

    var History = (function () {
        function History(delegate) {
            var _this = this;
            this.started = false;
            this.pageLoaded = false;
            this.onPopState = function (event) {
                if (_this.shouldHandlePopState()) {
                    var turbolinks = event.state.turbolinks;
                    if (turbolinks) {
                        var location_1 = Location.currentLocation;
                        var restorationIdentifier = turbolinks.restorationIdentifier;
                        _this.delegate.historyPoppedToLocationWithRestorationIdentifier(location_1, restorationIdentifier);
                    }
                }
            };
            this.onPageLoad = function (event) {
                defer(function () {
                    _this.pageLoaded = true;
                });
            };
            this.delegate = delegate;
        }
        History.prototype.start = function () {
            if (!this.started) {
                addEventListener("popstate", this.onPopState, false);
                addEventListener("load", this.onPageLoad, false);
                this.started = true;
            }
        };
        History.prototype.stop = function () {
            if (this.started) {
                removeEventListener("popstate", this.onPopState, false);
                removeEventListener("load", this.onPageLoad, false);
                this.started = false;
            }
        };
        History.prototype.push = function (location, restorationIdentifier) {
            this.update(history.pushState, location, restorationIdentifier);
        };
        History.prototype.replace = function (location, restorationIdentifier) {
            this.update(history.replaceState, location, restorationIdentifier);
        };
        History.prototype.shouldHandlePopState = function () {
            return this.pageIsLoaded();
        };
        History.prototype.pageIsLoaded = function () {
            return this.pageLoaded || document.readyState == "complete";
        };
        History.prototype.update = function (method, location, restorationIdentifier) {
            var state = { turbolinks: { restorationIdentifier: restorationIdentifier } };
            method.call(history, state, "", location.absoluteURL);
        };
        return History;
    }());
    //# sourceMappingURL=history.js.map

    var ScrollManager = (function () {
        function ScrollManager(delegate) {
            var _this = this;
            this.started = false;
            this.onScroll = function () {
                _this.updatePosition({ x: window.pageXOffset, y: window.pageYOffset });
            };
            this.delegate = delegate;
        }
        ScrollManager.prototype.start = function () {
            if (!this.started) {
                addEventListener("scroll", this.onScroll, false);
                this.onScroll();
                this.started = true;
            }
        };
        ScrollManager.prototype.stop = function () {
            if (this.started) {
                removeEventListener("scroll", this.onScroll, false);
                this.started = false;
            }
        };
        ScrollManager.prototype.scrollToElement = function (element) {
            element.scrollIntoView();
        };
        ScrollManager.prototype.scrollToPosition = function (_a) {
            var x = _a.x, y = _a.y;
            window.scrollTo(x, y);
        };
        ScrollManager.prototype.updatePosition = function (position) {
            this.delegate.scrollPositionChanged(position);
        };
        return ScrollManager;
    }());
    //# sourceMappingURL=scroll_manager.js.map

    var SnapshotCache = (function () {
        function SnapshotCache(size) {
            this.keys = [];
            this.snapshots = {};
            this.size = size;
        }
        SnapshotCache.prototype.has = function (location) {
            return location.toCacheKey() in this.snapshots;
        };
        SnapshotCache.prototype.get = function (location) {
            if (this.has(location)) {
                var snapshot = this.read(location);
                this.touch(location);
                return snapshot;
            }
        };
        SnapshotCache.prototype.put = function (location, snapshot) {
            this.write(location, snapshot);
            this.touch(location);
            return snapshot;
        };
        SnapshotCache.prototype.read = function (location) {
            return this.snapshots[location.toCacheKey()];
        };
        SnapshotCache.prototype.write = function (location, snapshot) {
            this.snapshots[location.toCacheKey()] = snapshot;
        };
        SnapshotCache.prototype.touch = function (location) {
            var key = location.toCacheKey();
            var index = this.keys.indexOf(key);
            if (index > -1)
                this.keys.splice(index, 1);
            this.keys.unshift(key);
            this.trim();
        };
        SnapshotCache.prototype.trim = function () {
            for (var _i = 0, _a = this.keys.splice(this.size); _i < _a.length; _i++) {
                var key = _a[_i];
                delete this.snapshots[key];
            }
        };
        return SnapshotCache;
    }());
    //# sourceMappingURL=snapshot_cache.js.map

    function isAction(action) {
        return action == "advance" || action == "replace" || action == "restore";
    }
    //# sourceMappingURL=types.js.map

    var Renderer = (function () {
        function Renderer() {
        }
        Renderer.prototype.renderView = function (callback) {
            this.delegate.viewWillRender(this.newBody);
            callback();
            this.delegate.viewRendered(this.newBody);
        };
        Renderer.prototype.invalidateView = function () {
            this.delegate.viewInvalidated();
        };
        Renderer.prototype.createScriptElement = function (element) {
            if (element.getAttribute("data-turbolinks-eval") == "false") {
                return element;
            }
            else {
                var createdScriptElement = document.createElement("script");
                createdScriptElement.textContent = element.textContent;
                createdScriptElement.async = false;
                copyElementAttributes(createdScriptElement, element);
                return createdScriptElement;
            }
        };
        return Renderer;
    }());
    function copyElementAttributes(destinationElement, sourceElement) {
        for (var _i = 0, _a = array(sourceElement.attributes); _i < _a.length; _i++) {
            var _b = _a[_i], name_1 = _b.name, value = _b.value;
            destinationElement.setAttribute(name_1, value);
        }
    }
    //# sourceMappingURL=renderer.js.map

    var ErrorRenderer = (function (_super) {
        __extends(ErrorRenderer, _super);
        function ErrorRenderer(delegate, html) {
            var _this = _super.call(this) || this;
            _this.delegate = delegate;
            _this.htmlElement = (function () {
                var htmlElement = document.createElement("html");
                htmlElement.innerHTML = html;
                return htmlElement;
            })();
            _this.newHead = _this.htmlElement.querySelector("head") || document.createElement("head");
            _this.newBody = _this.htmlElement.querySelector("body") || document.createElement("body");
            return _this;
        }
        ErrorRenderer.render = function (delegate, callback, html) {
            return new this(delegate, html).render(callback);
        };
        ErrorRenderer.prototype.render = function (callback) {
            var _this = this;
            this.renderView(function () {
                _this.replaceHeadAndBody();
                _this.activateBodyScriptElements();
                callback();
            });
        };
        ErrorRenderer.prototype.replaceHeadAndBody = function () {
            var documentElement = document.documentElement, head = document.head, body = document.body;
            documentElement.replaceChild(this.newHead, head);
            documentElement.replaceChild(this.newBody, body);
        };
        ErrorRenderer.prototype.activateBodyScriptElements = function () {
            for (var _i = 0, _a = this.getScriptElements(); _i < _a.length; _i++) {
                var replaceableElement = _a[_i];
                var parentNode = replaceableElement.parentNode;
                if (parentNode) {
                    var element = this.createScriptElement(replaceableElement);
                    parentNode.replaceChild(element, replaceableElement);
                }
            }
        };
        ErrorRenderer.prototype.getScriptElements = function () {
            return array(document.documentElement.querySelectorAll("script"));
        };
        return ErrorRenderer;
    }(Renderer));
    //# sourceMappingURL=error_renderer.js.map

    var HeadDetails = (function () {
        function HeadDetails(children) {
            this.detailsByOuterHTML = children.reduce(function (result, element) {
                var _a;
                var outerHTML = element.outerHTML;
                var details = outerHTML in result
                    ? result[outerHTML]
                    : {
                        type: elementType(element),
                        tracked: elementIsTracked(element),
                        elements: []
                    };
                return __assign({}, result, (_a = {}, _a[outerHTML] = __assign({}, details, { elements: details.elements.concat([element]) }), _a));
            }, {});
        }
        HeadDetails.fromHeadElement = function (headElement) {
            var children = headElement ? array(headElement.children) : [];
            return new this(children);
        };
        HeadDetails.prototype.getTrackedElementSignature = function () {
            var _this = this;
            return Object.keys(this.detailsByOuterHTML)
                .filter(function (outerHTML) { return _this.detailsByOuterHTML[outerHTML].tracked; })
                .join("");
        };
        HeadDetails.prototype.getScriptElementsNotInDetails = function (headDetails) {
            return this.getElementsMatchingTypeNotInDetails("script", headDetails);
        };
        HeadDetails.prototype.getStylesheetElementsNotInDetails = function (headDetails) {
            return this.getElementsMatchingTypeNotInDetails("stylesheet", headDetails);
        };
        HeadDetails.prototype.getElementsMatchingTypeNotInDetails = function (matchedType, headDetails) {
            var _this = this;
            return Object.keys(this.detailsByOuterHTML)
                .filter(function (outerHTML) { return !(outerHTML in headDetails.detailsByOuterHTML); })
                .map(function (outerHTML) { return _this.detailsByOuterHTML[outerHTML]; })
                .filter(function (_a) {
                var type = _a.type;
                return type == matchedType;
            })
                .map(function (_a) {
                var element = _a.elements[0];
                return element;
            });
        };
        HeadDetails.prototype.getProvisionalElements = function () {
            var _this = this;
            return Object.keys(this.detailsByOuterHTML).reduce(function (result, outerHTML) {
                var _a = _this.detailsByOuterHTML[outerHTML], type = _a.type, tracked = _a.tracked, elements = _a.elements;
                if (type == null && !tracked) {
                    return result.concat(elements);
                }
                else if (elements.length > 1) {
                    return result.concat(elements.slice(1));
                }
                else {
                    return result;
                }
            }, []);
        };
        HeadDetails.prototype.getMetaValue = function (name) {
            var element = this.findMetaElementByName(name);
            return element
                ? element.getAttribute("content")
                : null;
        };
        HeadDetails.prototype.findMetaElementByName = function (name) {
            var _this = this;
            return Object.keys(this.detailsByOuterHTML).reduce(function (result, outerHTML) {
                var element = _this.detailsByOuterHTML[outerHTML].elements[0];
                return elementIsMetaElementWithName(element, name) ? element : result;
            }, undefined);
        };
        return HeadDetails;
    }());
    function elementType(element) {
        if (elementIsScript(element)) {
            return "script";
        }
        else if (elementIsStylesheet(element)) {
            return "stylesheet";
        }
    }
    function elementIsTracked(element) {
        return element.getAttribute("data-turbolinks-track") == "reload";
    }
    function elementIsScript(element) {
        var tagName = element.tagName.toLowerCase();
        return tagName == "script";
    }
    function elementIsStylesheet(element) {
        var tagName = element.tagName.toLowerCase();
        return tagName == "style" || (tagName == "link" && element.getAttribute("rel") == "stylesheet");
    }
    function elementIsMetaElementWithName(element, name) {
        var tagName = element.tagName.toLowerCase();
        return tagName == "meta" && element.getAttribute("name") == name;
    }
    //# sourceMappingURL=head_details.js.map

    var Snapshot = (function () {
        function Snapshot(headDetails, bodyElement) {
            this.headDetails = headDetails;
            this.bodyElement = bodyElement;
        }
        Snapshot.wrap = function (value) {
            if (value instanceof this) {
                return value;
            }
            else if (typeof value == "string") {
                return this.fromHTMLString(value);
            }
            else {
                return this.fromHTMLElement(value);
            }
        };
        Snapshot.fromHTMLString = function (html) {
            var element = document.createElement("html");
            element.innerHTML = html;
            return this.fromHTMLElement(element);
        };
        Snapshot.fromHTMLElement = function (htmlElement) {
            var headElement = htmlElement.querySelector("head");
            var bodyElement = htmlElement.querySelector("body") || document.createElement("body");
            var headDetails = HeadDetails.fromHeadElement(headElement);
            return new this(headDetails, bodyElement);
        };
        Snapshot.prototype.clone = function () {
            return new Snapshot(this.headDetails, this.bodyElement.cloneNode(true));
        };
        Snapshot.prototype.getRootLocation = function () {
            var root = this.getSetting("root", "/");
            return new Location(root);
        };
        Snapshot.prototype.getCacheControlValue = function () {
            return this.getSetting("cache-control");
        };
        Snapshot.prototype.getElementForAnchor = function (anchor) {
            try {
                return this.bodyElement.querySelector("[id='" + anchor + "'], a[name='" + anchor + "']");
            }
            catch (_a) {
                return null;
            }
        };
        Snapshot.prototype.getPermanentElements = function () {
            return array(this.bodyElement.querySelectorAll("[id][data-turbolinks-permanent]"));
        };
        Snapshot.prototype.getPermanentElementById = function (id) {
            return this.bodyElement.querySelector("#" + id + "[data-turbolinks-permanent]");
        };
        Snapshot.prototype.getPermanentElementsPresentInSnapshot = function (snapshot) {
            return this.getPermanentElements().filter(function (_a) {
                var id = _a.id;
                return snapshot.getPermanentElementById(id);
            });
        };
        Snapshot.prototype.findFirstAutofocusableElement = function () {
            return this.bodyElement.querySelector("[autofocus]");
        };
        Snapshot.prototype.hasAnchor = function (anchor) {
            return this.getElementForAnchor(anchor) != null;
        };
        Snapshot.prototype.isPreviewable = function () {
            return this.getCacheControlValue() != "no-preview";
        };
        Snapshot.prototype.isCacheable = function () {
            return this.getCacheControlValue() != "no-cache";
        };
        Snapshot.prototype.isVisitable = function () {
            return this.getSetting("visit-control") != "reload";
        };
        Snapshot.prototype.getSetting = function (name, defaultValue) {
            var value = this.headDetails.getMetaValue("turbolinks-" + name);
            return value == null ? defaultValue : value;
        };
        return Snapshot;
    }());
    //# sourceMappingURL=snapshot.js.map

    var SnapshotRenderer = (function (_super) {
        __extends(SnapshotRenderer, _super);
        function SnapshotRenderer(delegate, currentSnapshot, newSnapshot, isPreview) {
            var _this = _super.call(this) || this;
            _this.delegate = delegate;
            _this.currentSnapshot = currentSnapshot;
            _this.currentHeadDetails = currentSnapshot.headDetails;
            _this.newSnapshot = newSnapshot;
            _this.newHeadDetails = newSnapshot.headDetails;
            _this.newBody = newSnapshot.bodyElement;
            _this.isPreview = isPreview;
            return _this;
        }
        SnapshotRenderer.render = function (delegate, callback, currentSnapshot, newSnapshot, isPreview) {
            return new this(delegate, currentSnapshot, newSnapshot, isPreview).render(callback);
        };
        SnapshotRenderer.prototype.render = function (callback) {
            var _this = this;
            if (this.shouldRender()) {
                this.mergeHead();
                this.renderView(function () {
                    _this.replaceBody();
                    if (!_this.isPreview) {
                        _this.focusFirstAutofocusableElement();
                    }
                    callback();
                });
            }
            else {
                this.invalidateView();
            }
        };
        SnapshotRenderer.prototype.mergeHead = function () {
            this.copyNewHeadStylesheetElements();
            this.copyNewHeadScriptElements();
            this.removeCurrentHeadProvisionalElements();
            this.copyNewHeadProvisionalElements();
        };
        SnapshotRenderer.prototype.replaceBody = function () {
            var placeholders = this.relocateCurrentBodyPermanentElements();
            this.activateNewBodyScriptElements();
            this.assignNewBody();
            this.replacePlaceholderElementsWithClonedPermanentElements(placeholders);
        };
        SnapshotRenderer.prototype.shouldRender = function () {
            return this.newSnapshot.isVisitable() && this.trackedElementsAreIdentical();
        };
        SnapshotRenderer.prototype.trackedElementsAreIdentical = function () {
            return this.currentHeadDetails.getTrackedElementSignature() == this.newHeadDetails.getTrackedElementSignature();
        };
        SnapshotRenderer.prototype.copyNewHeadStylesheetElements = function () {
            for (var _i = 0, _a = this.getNewHeadStylesheetElements(); _i < _a.length; _i++) {
                var element = _a[_i];
                document.head.appendChild(element);
            }
        };
        SnapshotRenderer.prototype.copyNewHeadScriptElements = function () {
            for (var _i = 0, _a = this.getNewHeadScriptElements(); _i < _a.length; _i++) {
                var element = _a[_i];
                document.head.appendChild(this.createScriptElement(element));
            }
        };
        SnapshotRenderer.prototype.removeCurrentHeadProvisionalElements = function () {
            for (var _i = 0, _a = this.getCurrentHeadProvisionalElements(); _i < _a.length; _i++) {
                var element = _a[_i];
                document.head.removeChild(element);
            }
        };
        SnapshotRenderer.prototype.copyNewHeadProvisionalElements = function () {
            for (var _i = 0, _a = this.getNewHeadProvisionalElements(); _i < _a.length; _i++) {
                var element = _a[_i];
                document.head.appendChild(element);
            }
        };
        SnapshotRenderer.prototype.relocateCurrentBodyPermanentElements = function () {
            var _this = this;
            return this.getCurrentBodyPermanentElements().reduce(function (placeholders, permanentElement) {
                var newElement = _this.newSnapshot.getPermanentElementById(permanentElement.id);
                if (newElement) {
                    var placeholder = createPlaceholderForPermanentElement(permanentElement);
                    replaceElementWithElement(permanentElement, placeholder.element);
                    replaceElementWithElement(newElement, permanentElement);
                    return placeholders.concat([placeholder]);
                }
                else {
                    return placeholders;
                }
            }, []);
        };
        SnapshotRenderer.prototype.replacePlaceholderElementsWithClonedPermanentElements = function (placeholders) {
            for (var _i = 0, placeholders_1 = placeholders; _i < placeholders_1.length; _i++) {
                var _a = placeholders_1[_i], element = _a.element, permanentElement = _a.permanentElement;
                var clonedElement = permanentElement.cloneNode(true);
                replaceElementWithElement(element, clonedElement);
            }
        };
        SnapshotRenderer.prototype.activateNewBodyScriptElements = function () {
            for (var _i = 0, _a = this.getNewBodyScriptElements(); _i < _a.length; _i++) {
                var inertScriptElement = _a[_i];
                var activatedScriptElement = this.createScriptElement(inertScriptElement);
                replaceElementWithElement(inertScriptElement, activatedScriptElement);
            }
        };
        SnapshotRenderer.prototype.assignNewBody = function () {
            replaceElementWithElement(document.body, this.newBody);
        };
        SnapshotRenderer.prototype.focusFirstAutofocusableElement = function () {
            var element = this.newSnapshot.findFirstAutofocusableElement();
            if (elementIsFocusable(element)) {
                element.focus();
            }
        };
        SnapshotRenderer.prototype.getNewHeadStylesheetElements = function () {
            return this.newHeadDetails.getStylesheetElementsNotInDetails(this.currentHeadDetails);
        };
        SnapshotRenderer.prototype.getNewHeadScriptElements = function () {
            return this.newHeadDetails.getScriptElementsNotInDetails(this.currentHeadDetails);
        };
        SnapshotRenderer.prototype.getCurrentHeadProvisionalElements = function () {
            return this.currentHeadDetails.getProvisionalElements();
        };
        SnapshotRenderer.prototype.getNewHeadProvisionalElements = function () {
            return this.newHeadDetails.getProvisionalElements();
        };
        SnapshotRenderer.prototype.getCurrentBodyPermanentElements = function () {
            return this.currentSnapshot.getPermanentElementsPresentInSnapshot(this.newSnapshot);
        };
        SnapshotRenderer.prototype.getNewBodyScriptElements = function () {
            return array(this.newBody.querySelectorAll("script"));
        };
        return SnapshotRenderer;
    }(Renderer));
    function createPlaceholderForPermanentElement(permanentElement) {
        var element = document.createElement("meta");
        element.setAttribute("name", "turbolinks-permanent-placeholder");
        element.setAttribute("content", permanentElement.id);
        return { element: element, permanentElement: permanentElement };
    }
    function replaceElementWithElement(fromElement, toElement) {
        var parentElement = fromElement.parentElement;
        if (parentElement) {
            return parentElement.replaceChild(toElement, fromElement);
        }
    }
    function elementIsFocusable(element) {
        return element && typeof element.focus == "function";
    }

    var View = (function () {
        function View(delegate) {
            this.htmlElement = document.documentElement;
            this.delegate = delegate;
        }
        View.prototype.getRootLocation = function () {
            return this.getSnapshot().getRootLocation();
        };
        View.prototype.getElementForAnchor = function (anchor) {
            return this.getSnapshot().getElementForAnchor(anchor);
        };
        View.prototype.getSnapshot = function () {
            return Snapshot.fromHTMLElement(this.htmlElement);
        };
        View.prototype.render = function (_a, callback) {
            var snapshot = _a.snapshot, error = _a.error, isPreview = _a.isPreview;
            this.markAsPreview(isPreview);
            if (snapshot) {
                this.renderSnapshot(snapshot, isPreview, callback);
            }
            else {
                this.renderError(error, callback);
            }
        };
        View.prototype.markAsPreview = function (isPreview) {
            if (isPreview) {
                this.htmlElement.setAttribute("data-turbolinks-preview", "");
            }
            else {
                this.htmlElement.removeAttribute("data-turbolinks-preview");
            }
        };
        View.prototype.renderSnapshot = function (snapshot, isPreview, callback) {
            SnapshotRenderer.render(this.delegate, callback, this.getSnapshot(), snapshot, isPreview || false);
        };
        View.prototype.renderError = function (error, callback) {
            ErrorRenderer.render(this.delegate, callback, error || "");
        };
        return View;
    }());
    //# sourceMappingURL=view.js.map

    var TimingMetric;
    (function (TimingMetric) {
        TimingMetric["visitStart"] = "visitStart";
        TimingMetric["requestStart"] = "requestStart";
        TimingMetric["requestEnd"] = "requestEnd";
        TimingMetric["visitEnd"] = "visitEnd";
    })(TimingMetric || (TimingMetric = {}));
    var VisitState;
    (function (VisitState) {
        VisitState["initialized"] = "initialized";
        VisitState["started"] = "started";
        VisitState["canceled"] = "canceled";
        VisitState["failed"] = "failed";
        VisitState["completed"] = "completed";
    })(VisitState || (VisitState = {}));
    var Visit = (function () {
        function Visit(controller, location, action, restorationIdentifier) {
            if (restorationIdentifier === void 0) { restorationIdentifier = uuid(); }
            var _this = this;
            this.identifier = uuid();
            this.timingMetrics = {};
            this.followedRedirect = false;
            this.historyChanged = false;
            this.progress = 0;
            this.scrolled = false;
            this.snapshotCached = false;
            this.state = VisitState.initialized;
            this.performScroll = function () {
                if (!_this.scrolled) {
                    if (_this.action == "restore") {
                        _this.scrollToRestoredPosition() || _this.scrollToTop();
                    }
                    else {
                        _this.scrollToAnchor() || _this.scrollToTop();
                    }
                    _this.scrolled = true;
                }
            };
            this.controller = controller;
            this.location = location;
            this.action = action;
            this.adapter = controller.adapter;
            this.restorationIdentifier = restorationIdentifier;
        }
        Visit.prototype.start = function () {
            if (this.state == VisitState.initialized) {
                this.recordTimingMetric(TimingMetric.visitStart);
                this.state = VisitState.started;
                this.adapter.visitStarted(this);
            }
        };
        Visit.prototype.cancel = function () {
            if (this.state == VisitState.started) {
                if (this.request) {
                    this.request.cancel();
                }
                this.cancelRender();
                this.state = VisitState.canceled;
            }
        };
        Visit.prototype.complete = function () {
            if (this.state == VisitState.started) {
                this.recordTimingMetric(TimingMetric.visitEnd);
                this.state = VisitState.completed;
                this.adapter.visitCompleted(this);
                this.controller.visitCompleted(this);
            }
        };
        Visit.prototype.fail = function () {
            if (this.state == VisitState.started) {
                this.state = VisitState.failed;
                this.adapter.visitFailed(this);
            }
        };
        Visit.prototype.changeHistory = function () {
            if (!this.historyChanged) {
                var actionForHistory = this.location.isEqualTo(this.referrer) ? "replace" : this.action;
                var method = this.getHistoryMethodForAction(actionForHistory);
                method.call(this.controller, this.location, this.restorationIdentifier);
                this.historyChanged = true;
            }
        };
        Visit.prototype.issueRequest = function () {
            if (this.shouldIssueRequest() && !this.request) {
                this.progress = 0;
                this.request = new HttpRequest(this, this.location, this.referrer);
                this.request.send();
            }
        };
        Visit.prototype.getCachedSnapshot = function () {
            var snapshot = this.controller.getCachedSnapshotForLocation(this.location);
            if (snapshot && (!this.location.anchor || snapshot.hasAnchor(this.location.anchor))) {
                if (this.action == "restore" || snapshot.isPreviewable()) {
                    return snapshot;
                }
            }
        };
        Visit.prototype.hasCachedSnapshot = function () {
            return this.getCachedSnapshot() != null;
        };
        Visit.prototype.loadCachedSnapshot = function () {
            var _this = this;
            var snapshot = this.getCachedSnapshot();
            if (snapshot) {
                var isPreview_1 = this.shouldIssueRequest();
                this.render(function () {
                    _this.cacheSnapshot();
                    _this.controller.render({ snapshot: snapshot, isPreview: isPreview_1 }, _this.performScroll);
                    _this.adapter.visitRendered(_this);
                    if (!isPreview_1) {
                        _this.complete();
                    }
                });
            }
        };
        Visit.prototype.loadResponse = function () {
            var _this = this;
            var _a = this, request = _a.request, response = _a.response;
            if (request && response) {
                this.render(function () {
                    _this.cacheSnapshot();
                    if (request.failed) {
                        _this.controller.render({ error: _this.response }, _this.performScroll);
                        _this.adapter.visitRendered(_this);
                        _this.fail();
                    }
                    else {
                        _this.controller.render({ snapshot: Snapshot.fromHTMLString(response) }, _this.performScroll);
                        _this.adapter.visitRendered(_this);
                        _this.complete();
                    }
                });
            }
        };
        Visit.prototype.followRedirect = function () {
            if (this.redirectedToLocation && !this.followedRedirect) {
                this.location = this.redirectedToLocation;
                this.controller.replaceHistoryWithLocationAndRestorationIdentifier(this.redirectedToLocation, this.restorationIdentifier);
                this.followedRedirect = true;
            }
        };
        Visit.prototype.requestStarted = function () {
            this.recordTimingMetric(TimingMetric.requestStart);
            this.adapter.visitRequestStarted(this);
        };
        Visit.prototype.requestProgressed = function (progress) {
            this.progress = progress;
            if (this.adapter.visitRequestProgressed) {
                this.adapter.visitRequestProgressed(this);
            }
        };
        Visit.prototype.requestCompletedWithResponse = function (response, redirectedToLocation) {
            this.response = response;
            this.redirectedToLocation = redirectedToLocation;
            this.adapter.visitRequestCompleted(this);
        };
        Visit.prototype.requestFailedWithStatusCode = function (statusCode, response) {
            this.response = response;
            this.adapter.visitRequestFailedWithStatusCode(this, statusCode);
        };
        Visit.prototype.requestFinished = function () {
            this.recordTimingMetric(TimingMetric.requestEnd);
            this.adapter.visitRequestFinished(this);
        };
        Visit.prototype.scrollToRestoredPosition = function () {
            var position = this.restorationData ? this.restorationData.scrollPosition : undefined;
            if (position) {
                this.controller.scrollToPosition(position);
                return true;
            }
        };
        Visit.prototype.scrollToAnchor = function () {
            if (this.location.anchor != null) {
                this.controller.scrollToAnchor(this.location.anchor);
                return true;
            }
        };
        Visit.prototype.scrollToTop = function () {
            this.controller.scrollToPosition({ x: 0, y: 0 });
        };
        Visit.prototype.recordTimingMetric = function (metric) {
            this.timingMetrics[metric] = new Date().getTime();
        };
        Visit.prototype.getTimingMetrics = function () {
            return __assign({}, this.timingMetrics);
        };
        Visit.prototype.getHistoryMethodForAction = function (action) {
            switch (action) {
                case "replace": return this.controller.replaceHistoryWithLocationAndRestorationIdentifier;
                case "advance":
                case "restore": return this.controller.pushHistoryWithLocationAndRestorationIdentifier;
            }
        };
        Visit.prototype.shouldIssueRequest = function () {
            return this.action == "restore"
                ? !this.hasCachedSnapshot()
                : true;
        };
        Visit.prototype.cacheSnapshot = function () {
            if (!this.snapshotCached) {
                this.controller.cacheSnapshot();
                this.snapshotCached = true;
            }
        };
        Visit.prototype.render = function (callback) {
            var _this = this;
            this.cancelRender();
            this.frame = requestAnimationFrame(function () {
                delete _this.frame;
                callback.call(_this);
            });
        };
        Visit.prototype.cancelRender = function () {
            if (this.frame) {
                cancelAnimationFrame(this.frame);
                delete this.frame;
            }
        };
        return Visit;
    }());
    //# sourceMappingURL=visit.js.map

    var Controller = (function () {
        function Controller() {
            var _this = this;
            this.adapter = new BrowserAdapter(this);
            this.history = new History(this);
            this.restorationData = {};
            this.scrollManager = new ScrollManager(this);
            this.view = new View(this);
            this.cache = new SnapshotCache(10);
            this.enabled = true;
            this.progressBarDelay = 500;
            this.started = false;
            this.pageLoaded = function () {
                _this.lastRenderedLocation = _this.location;
                _this.notifyApplicationAfterPageLoad();
            };
            this.clickCaptured = function () {
                removeEventListener("click", _this.clickBubbled, false);
                addEventListener("click", _this.clickBubbled, false);
            };
            this.clickBubbled = function (event) {
                if (_this.enabled && _this.clickEventIsSignificant(event)) {
                    var link = _this.getVisitableLinkForTarget(event.target);
                    if (link) {
                        var location_1 = _this.getVisitableLocationForLink(link);
                        if (location_1 && _this.applicationAllowsFollowingLinkToLocation(link, location_1)) {
                            event.preventDefault();
                            var action = _this.getActionForLink(link);
                            _this.visit(location_1, { action: action });
                        }
                    }
                }
            };
        }
        Controller.prototype.start = function () {
            if (Controller.supported && !this.started) {
                addEventListener("click", this.clickCaptured, true);
                addEventListener("DOMContentLoaded", this.pageLoaded, false);
                this.scrollManager.start();
                this.startHistory();
                this.started = true;
                this.enabled = true;
            }
        };
        Controller.prototype.disable = function () {
            this.enabled = false;
        };
        Controller.prototype.stop = function () {
            if (this.started) {
                removeEventListener("click", this.clickCaptured, true);
                removeEventListener("DOMContentLoaded", this.pageLoaded, false);
                this.scrollManager.stop();
                this.stopHistory();
                this.started = false;
            }
        };
        Controller.prototype.clearCache = function () {
            this.cache = new SnapshotCache(10);
        };
        Controller.prototype.visit = function (location, options) {
            if (options === void 0) { options = {}; }
            location = Location.wrap(location);
            if (this.applicationAllowsVisitingLocation(location)) {
                if (this.locationIsVisitable(location)) {
                    var action = options.action || "advance";
                    this.adapter.visitProposedToLocationWithAction(location, action);
                }
                else {
                    window.location.href = location.toString();
                }
            }
        };
        Controller.prototype.startVisitToLocationWithAction = function (location, action, restorationIdentifier) {
            if (Controller.supported) {
                var restorationData = this.getRestorationDataForIdentifier(restorationIdentifier);
                this.startVisit(Location.wrap(location), action, { restorationData: restorationData });
            }
            else {
                window.location.href = location.toString();
            }
        };
        Controller.prototype.setProgressBarDelay = function (delay) {
            this.progressBarDelay = delay;
        };
        Controller.prototype.startHistory = function () {
            this.location = Location.currentLocation;
            this.restorationIdentifier = uuid();
            this.history.start();
            this.history.replace(this.location, this.restorationIdentifier);
        };
        Controller.prototype.stopHistory = function () {
            this.history.stop();
        };
        Controller.prototype.pushHistoryWithLocationAndRestorationIdentifier = function (locatable, restorationIdentifier) {
            this.location = Location.wrap(locatable);
            this.restorationIdentifier = restorationIdentifier;
            this.history.push(this.location, this.restorationIdentifier);
        };
        Controller.prototype.replaceHistoryWithLocationAndRestorationIdentifier = function (locatable, restorationIdentifier) {
            this.location = Location.wrap(locatable);
            this.restorationIdentifier = restorationIdentifier;
            this.history.replace(this.location, this.restorationIdentifier);
        };
        Controller.prototype.historyPoppedToLocationWithRestorationIdentifier = function (location, restorationIdentifier) {
            if (this.enabled) {
                this.location = location;
                this.restorationIdentifier = restorationIdentifier;
                var restorationData = this.getRestorationDataForIdentifier(restorationIdentifier);
                this.startVisit(location, "restore", { restorationIdentifier: restorationIdentifier, restorationData: restorationData, historyChanged: true });
            }
            else {
                this.adapter.pageInvalidated();
            }
        };
        Controller.prototype.getCachedSnapshotForLocation = function (location) {
            var snapshot = this.cache.get(location);
            return snapshot ? snapshot.clone() : snapshot;
        };
        Controller.prototype.shouldCacheSnapshot = function () {
            return this.view.getSnapshot().isCacheable();
        };
        Controller.prototype.cacheSnapshot = function () {
            var _this = this;
            if (this.shouldCacheSnapshot()) {
                this.notifyApplicationBeforeCachingSnapshot();
                var snapshot_1 = this.view.getSnapshot();
                var location_2 = this.lastRenderedLocation || Location.currentLocation;
                defer(function () { return _this.cache.put(location_2, snapshot_1.clone()); });
            }
        };
        Controller.prototype.scrollToAnchor = function (anchor) {
            var element = this.view.getElementForAnchor(anchor);
            if (element) {
                this.scrollToElement(element);
            }
            else {
                this.scrollToPosition({ x: 0, y: 0 });
            }
        };
        Controller.prototype.scrollToElement = function (element) {
            this.scrollManager.scrollToElement(element);
        };
        Controller.prototype.scrollToPosition = function (position) {
            this.scrollManager.scrollToPosition(position);
        };
        Controller.prototype.scrollPositionChanged = function (position) {
            var restorationData = this.getCurrentRestorationData();
            restorationData.scrollPosition = position;
        };
        Controller.prototype.render = function (options, callback) {
            this.view.render(options, callback);
        };
        Controller.prototype.viewInvalidated = function () {
            this.adapter.pageInvalidated();
        };
        Controller.prototype.viewWillRender = function (newBody) {
            this.notifyApplicationBeforeRender(newBody);
        };
        Controller.prototype.viewRendered = function () {
            this.lastRenderedLocation = this.currentVisit.location;
            this.notifyApplicationAfterRender();
        };
        Controller.prototype.applicationAllowsFollowingLinkToLocation = function (link, location) {
            var event = this.notifyApplicationAfterClickingLinkToLocation(link, location);
            return !event.defaultPrevented;
        };
        Controller.prototype.applicationAllowsVisitingLocation = function (location) {
            var event = this.notifyApplicationBeforeVisitingLocation(location);
            return !event.defaultPrevented;
        };
        Controller.prototype.notifyApplicationAfterClickingLinkToLocation = function (link, location) {
            return dispatch("turbolinks:click", { target: link, data: { url: location.absoluteURL }, cancelable: true });
        };
        Controller.prototype.notifyApplicationBeforeVisitingLocation = function (location) {
            return dispatch("turbolinks:before-visit", { data: { url: location.absoluteURL }, cancelable: true });
        };
        Controller.prototype.notifyApplicationAfterVisitingLocation = function (location) {
            return dispatch("turbolinks:visit", { data: { url: location.absoluteURL } });
        };
        Controller.prototype.notifyApplicationBeforeCachingSnapshot = function () {
            return dispatch("turbolinks:before-cache");
        };
        Controller.prototype.notifyApplicationBeforeRender = function (newBody) {
            return dispatch("turbolinks:before-render", { data: { newBody: newBody } });
        };
        Controller.prototype.notifyApplicationAfterRender = function () {
            return dispatch("turbolinks:render");
        };
        Controller.prototype.notifyApplicationAfterPageLoad = function (timing) {
            if (timing === void 0) { timing = {}; }
            return dispatch("turbolinks:load", { data: { url: this.location.absoluteURL, timing: timing } });
        };
        Controller.prototype.startVisit = function (location, action, properties) {
            if (this.currentVisit) {
                this.currentVisit.cancel();
            }
            this.currentVisit = this.createVisit(location, action, properties);
            this.currentVisit.start();
            this.notifyApplicationAfterVisitingLocation(location);
        };
        Controller.prototype.createVisit = function (location, action, properties) {
            var visit = new Visit(this, location, action, properties.restorationIdentifier);
            visit.restorationData = __assign({}, (properties.restorationData || {}));
            visit.historyChanged = !!properties.historyChanged;
            visit.referrer = this.location;
            return visit;
        };
        Controller.prototype.visitCompleted = function (visit) {
            this.notifyApplicationAfterPageLoad(visit.getTimingMetrics());
        };
        Controller.prototype.clickEventIsSignificant = function (event) {
            return !((event.target && event.target.isContentEditable)
                || event.defaultPrevented
                || event.which > 1
                || event.altKey
                || event.ctrlKey
                || event.metaKey
                || event.shiftKey);
        };
        Controller.prototype.getVisitableLinkForTarget = function (target) {
            if (target instanceof Element && this.elementIsVisitable(target)) {
                return closest(target, "a[href]:not([target]):not([download])");
            }
        };
        Controller.prototype.getVisitableLocationForLink = function (link) {
            var location = new Location(link.getAttribute("href") || "");
            if (this.locationIsVisitable(location)) {
                return location;
            }
        };
        Controller.prototype.getActionForLink = function (link) {
            var action = link.getAttribute("data-turbolinks-action");
            return isAction(action) ? action : "advance";
        };
        Controller.prototype.elementIsVisitable = function (element) {
            var container = closest(element, "[data-turbolinks]");
            if (container) {
                return container.getAttribute("data-turbolinks") != "false";
            }
            else {
                return true;
            }
        };
        Controller.prototype.locationIsVisitable = function (location) {
            return location.isPrefixedBy(this.view.getRootLocation()) && location.isHTML();
        };
        Controller.prototype.getCurrentRestorationData = function () {
            return this.getRestorationDataForIdentifier(this.restorationIdentifier);
        };
        Controller.prototype.getRestorationDataForIdentifier = function (identifier) {
            if (!(identifier in this.restorationData)) {
                this.restorationData[identifier] = {};
            }
            return this.restorationData[identifier];
        };
        Controller.supported = !!(window.history.pushState &&
            window.requestAnimationFrame &&
            window.addEventListener);
        return Controller;
    }());
    //# sourceMappingURL=controller.js.map

    var controller = new Controller;
    var namespace = {
        get supported() {
            return Controller.supported;
        },
        controller: controller,
        visit: function (location, options) {
            controller.visit(location, options);
        },
        clearCache: function () {
            controller.clearCache();
        },
        setProgressBarDelay: function (delay) {
            controller.setProgressBarDelay(delay);
        },
        start: function () {
            controller.start();
        }
    };
    //# sourceMappingURL=namespace.js.map

    (function () {
        var element = document.currentScript;
        if (!element)
            return;
        if (element.hasAttribute("data-turbolinks-suppress-warning"))
            return;
        while (element = element.parentElement) {
            if (element == document.body) {
                return console.warn(unindent(templateObject_1$1 || (templateObject_1$1 = __makeTemplateObject(["\n        You are loading Turbolinks from a <script> element inside the <body> element. This is probably not what you meant to do!\n\n        Load your application\u2019s JavaScript bundle inside the <head> element instead. <script> elements in <body> are evaluated with each page change.\n\n        For more information, see: https://github.com/turbolinks/turbolinks#working-with-script-elements\n\n        \u2014\u2014\n        Suppress this warning by adding a \"data-turbolinks-suppress-warning\" attribute to: %s\n      "], ["\n        You are loading Turbolinks from a <script> element inside the <body> element. This is probably not what you meant to do!\n\n        Load your application\u2019s JavaScript bundle inside the <head> element instead. <script> elements in <body> are evaluated with each page change.\n\n        For more information, see: https://github.com/turbolinks/turbolinks#working-with-script-elements\n\n        \u2014\u2014\n        Suppress this warning by adding a \"data-turbolinks-suppress-warning\" attribute to: %s\n      "]))), element.outerHTML);
            }
        }
    })();
    var templateObject_1$1;
    //# sourceMappingURL=script_warning.js.map

    if (!window.Turbolinks) {
        window.Turbolinks = namespace;
        if (!isAMD() && !isCommonJS()) {
            namespace.start();
        }
    }
    function isAMD() {
        return typeof define == "function" && define.amd;
    }
    function isCommonJS() {
        return typeof exports == "object" && typeof module != "undefined";
    }
    //# sourceMappingURL=index.js.map

    return namespace;

}));
//# sourceMappingURL=turbolinks.js.map
