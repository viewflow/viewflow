(function (Turbolinks, materialComponentsWeb) {
  'use strict';

  function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

  var Turbolinks__default = /*#__PURE__*/_interopDefaultLegacy(Turbolinks);

  const equalFn = (a, b) => a === b;
  const ERROR = Symbol("error");
  const NOTPENDING = {};
  const STALE = 1;
  const PENDING = 2;
  const UNOWNED = {
    owned: null,
    cleanups: null,
    context: null,
    owner: null
  };
  let Owner = null;
  let Listener = null;
  let Pending = null;
  let Updates = null;
  let Afters = [];
  let ExecCount = 0;
  function createRoot(fn, detachedOwner) {
    detachedOwner && (Owner = detachedOwner);
    const listener = Listener,
          owner = Owner,
          root = fn.length === 0 ? UNOWNED : {
      owned: null,
      cleanups: null,
      context: null,
      owner
    };
    Owner = root;
    Listener = null;
    let result;
    try {
      result = fn(() => cleanNode(root));
    } catch (err) {
      const fns = lookup(Owner, ERROR);
      if (!fns) throw err;
      fns.forEach(f => f(err));
    } finally {
      while (Afters.length) Afters.shift()();
      Listener = listener;
      Owner = owner;
    }
    return result;
  }
  function createSignal(value, areEqual) {
    const s = {
      value,
      observers: null,
      observerSlots: null,
      pending: NOTPENDING,
      comparator: areEqual ? typeof areEqual === "function" ? areEqual : equalFn : undefined
    };
    return [readSignal.bind(s), writeSignal.bind(s)];
  }
  function createEffect(fn, value) {
    updateComputation(createComputation(fn, value));
  }
  function createMemo(fn, value, areEqual) {
    const c = createComputation(fn, value);
    c.pending = NOTPENDING;
    c.observers = null;
    c.observerSlots = null;
    c.comparator = areEqual ? typeof areEqual === "function" ? areEqual : equalFn : undefined;
    updateComputation(c);
    return readSignal.bind(c);
  }
  function freeze(fn) {
    let pending = Pending,
        q = Pending = [];
    const result = fn();
    Pending = pending;
    runUpdates(() => {
      for (let i = 0; i < q.length; i += 1) {
        const data = q[i];
        if (data.pending !== NOTPENDING) {
          const pending = data.pending;
          data.pending = NOTPENDING;
          writeSignal.call(data, pending);
        }
      }
    });
    return result;
  }
  function sample(fn) {
    let result,
        listener = Listener;
    Listener = null;
    result = fn();
    Listener = listener;
    return result;
  }
  function afterEffects(fn) {
    Afters.push(fn);
  }
  function onCleanup(fn) {
    if (Owner === null) console.warn("cleanups created outside a `createRoot` or `render` will never be run");else if (Owner.cleanups === null) Owner.cleanups = [fn];else Owner.cleanups.push(fn);
    return fn;
  }
  function isListening() {
    return Listener !== null;
  }
  function readSignal() {
    if (this.state && this.sources) {
      const updates = Updates;
      Updates = null;
      this.state === STALE ? updateComputation(this) : lookDownstream(this);
      Updates = updates;
    }
    if (Listener) {
      const sSlot = this.observers ? this.observers.length : 0;
      if (!Listener.sources) {
        Listener.sources = [this];
        Listener.sourceSlots = [sSlot];
      } else {
        Listener.sources.push(this);
        Listener.sourceSlots.push(sSlot);
      }
      if (!this.observers) {
        this.observers = [Listener];
        this.observerSlots = [Listener.sources.length - 1];
      } else {
        this.observers.push(Listener);
        this.observerSlots.push(Listener.sources.length - 1);
      }
    }
    return this.value;
  }
  function writeSignal(value) {
    if (this.comparator && this.comparator(this.value, value)) return value;
    if (Pending) {
      if (this.pending === NOTPENDING) Pending.push(this);
      this.pending = value;
      return value;
    }
    this.value = value;
    if (this.observers && (!Updates || this.observers.length)) {
      runUpdates(() => {
        for (let i = 0; i < this.observers.length; i += 1) {
          const o = this.observers[i];
          if (o.observers && o.state !== PENDING) markUpstream(o);
          o.state = STALE;
          if (Updates.length > 10e5) throw new Error("Potential Infinite Loop Detected.");
          Updates.push(o);
        }
      });
    }
    return value;
  }
  function updateComputation(node) {
    if (!node.fn) return;
    cleanNode(node);
    const owner = Owner,
          listener = Listener,
          time = ExecCount;
    Listener = Owner = node;
    const nextValue = node.fn(node.value);
    if (!node.updatedAt || node.updatedAt <= time) {
      if (node.observers && node.observers.length) {
        writeSignal.call(node, nextValue);
      } else node.value = nextValue;
      node.updatedAt = time;
    }
    Listener = listener;
    Owner = owner;
  }
  function createComputation(fn, init) {
    const c = {
      fn,
      state: 0,
      updatedAt: null,
      owned: null,
      sources: null,
      sourceSlots: null,
      cleanups: null,
      value: init,
      owner: Owner,
      context: null
    };
    if (Owner === null) console.warn("computations created outside a `createRoot` or `render` will never be disposed");else if (Owner !== UNOWNED) {
      if (!Owner.owned) Owner.owned = [c];else Owner.owned.push(c);
    }
    return c;
  }
  function runTop(node) {
    let top = node.state === STALE && node;
    while (node.fn && (node = node.owner)) node.state === STALE && (top = node);
    top && updateComputation(top);
  }
  function runUpdates(fn) {
    if (Updates) return fn();
    Updates = [];
    ExecCount++;
    try {
      fn();
      for (let i = 0; i < Updates.length; i += 1) {
        try {
          runTop(Updates[i]);
        } catch (err) {
          const fns = lookup(Owner, ERROR);
          if (!fns) throw err;
          fns.forEach(f => f(err));
        }
      }
    } finally {
      Updates = null;
      while (Afters.length) Afters.shift()();
    }
  }
  function lookDownstream(node) {
    node.state = 0;
    for (let i = 0; i < node.sources.length; i += 1) {
      const source = node.sources[i];
      if (source.sources) {
        if (source.state === STALE) runTop(source);else if (source.state === PENDING) lookDownstream(source);
      }
    }
  }
  function markUpstream(node) {
    for (let i = 0; i < node.observers.length; i += 1) {
      const o = node.observers[i];
      if (!o.state) {
        o.state = PENDING;
        o.observers && markUpstream(o);
      }
    }
  }
  function cleanNode(node) {
    let i;
    if (node.sources) {
      while (node.sources.length) {
        const source = node.sources.pop(),
              index = node.sourceSlots.pop(),
              obs = source.observers;
        if (obs && obs.length) {
          const n = obs.pop(),
                s = source.observerSlots.pop();
          if (index < obs.length) {
            n.sourceSlots[s] = index;
            obs[index] = n;
            source.observerSlots[index] = s;
          }
        }
      }
      node.state = 0;
    }
    if (node.owned) {
      for (i = 0; i < node.owned.length; i++) cleanNode(node.owned[i]);
      node.owned = null;
    }
    if (node.cleanups) {
      for (i = 0; i < node.cleanups.length; i++) node.cleanups[i]();
      node.cleanups = null;
    }
  }
  function lookup(owner, key) {
    return owner && (owner.context && owner.context[key] || owner.owner && lookup(owner.owner, key));
  }

  const $RAW = Symbol("state-raw"),
        $NODE = Symbol("state-node"),
        $PROXY = Symbol("state-proxy");
  function wrap(value, traps) {
    return value[$PROXY] || (value[$PROXY] = new Proxy(value, traps || proxyTraps));
  }
  function isWrappable(obj) {
    return obj != null && typeof obj === "object" && (obj.__proto__ === Object.prototype || Array.isArray(obj));
  }
  function unwrap(item) {
    let result, unwrapped, v;
    if (result = item != null && item[$RAW]) return result;
    if (!isWrappable(item)) return item;
    if (Array.isArray(item)) {
      if (Object.isFrozen(item)) item = item.slice(0);
      for (let i = 0, l = item.length; i < l; i++) {
        v = item[i];
        if ((unwrapped = unwrap(v)) !== v) item[i] = unwrapped;
      }
    } else {
      if (Object.isFrozen(item)) item = Object.assign({}, item);
      let keys = Object.keys(item);
      for (let i = 0, l = keys.length; i < l; i++) {
        v = item[keys[i]];
        if ((unwrapped = unwrap(v)) !== v) item[keys[i]] = unwrapped;
      }
    }
    return item;
  }
  function getDataNodes(target) {
    let nodes = target[$NODE];
    if (!nodes) target[$NODE] = nodes = {};
    return nodes;
  }
  const proxyTraps = {
    get(target, property) {
      if (property === $RAW) return target;
      if (property === $PROXY || property === $NODE) return;
      const value = target[property],
            wrappable = isWrappable(value);
      if (isListening() && (typeof value !== "function" || target.hasOwnProperty(property))) {
        let nodes, node;
        if (wrappable && (nodes = getDataNodes(value))) {
          node = nodes._ || (nodes._ = createSignal());
          node[0]();
        }
        nodes = getDataNodes(target);
        node = nodes[property] || (nodes[property] = createSignal());
        node[0]();
      }
      return wrappable ? wrap(value) : value;
    },
    set() {
      return true;
    },
    deleteProperty() {
      return true;
    }
  };
  const setterTraps = {
    get(target, property) {
      if (property === $RAW) return target;
      const value = target[property];
      return isWrappable(value) ? new Proxy(value, setterTraps) : value;
    },
    set(target, property, value) {
      setProperty(target, property, unwrap(value));
      return true;
    },
    deleteProperty(target, property) {
      setProperty(target, property, undefined);
      return true;
    }
  };
  function setProperty(state, property, value, force) {
    if (!force && state[property] === value) return;
    const notify = Array.isArray(state) || !(property in state);
    if (value === undefined) {
      delete state[property];
    } else state[property] = value;
    let nodes = getDataNodes(state),
        node;
    (node = nodes[property]) && node[1]();
    notify && (node = nodes._) && node[1]();
  }
  function mergeState(state, value, force) {
    const keys = Object.keys(value);
    for (let i = 0; i < keys.length; i += 1) {
      const key = keys[i];
      setProperty(state, key, value[key], force);
    }
  }
  function updatePath(current, path, traversed = []) {
    let part,
        next = current;
    if (path.length > 1) {
      part = path.shift();
      const partType = typeof part,
            isArray = Array.isArray(current);
      if (Array.isArray(part)) {
        for (let i = 0; i < part.length; i++) {
          updatePath(current, [part[i]].concat(path), [part[i]].concat(traversed));
        }
        return;
      } else if (isArray && partType === "function") {
        for (let i = 0; i < current.length; i++) {
          if (part(current[i], i)) updatePath(current, [i].concat(path), [i].concat(traversed));
        }
        return;
      } else if (isArray && partType === "object") {
        const {
          from = 0,
          to = current.length - 1,
          by = 1
        } = part;
        for (let i = from; i <= to; i += by) {
          updatePath(current, [i].concat(path), [i].concat(traversed));
        }
        return;
      } else if (path.length > 1) {
        updatePath(current[part], path, [part].concat(traversed));
        return;
      }
      next = current[part];
      traversed = [part].concat(traversed);
    }
    let value = path[0];
    if (typeof value === "function") {
      const wrapped = part === undefined || isWrappable(next) ? new Proxy(next, setterTraps) : next;
      value = value(wrapped, traversed);
      if (value === wrapped || value === undefined) return;
    }
    value = unwrap(value);
    if (part === undefined || isWrappable(next) && isWrappable(value) && !Array.isArray(value)) {
      mergeState(next, value);
    } else setProperty(current, part, value);
  }
  function createState(state) {
    const unwrappedState = unwrap(state || {});
    const wrappedState = wrap(unwrappedState);
    function setState(...args) {
      freeze(() => updatePath(unwrappedState, args));
    }
    return [wrappedState, setState];
  }

  function dynamicProperty(props, key) {
    const src = props[key];
    Object.defineProperty(props, key, {
      get() {
        return src();
      },
      enumerable: true
    });
  }
  function createComponent(Comp, props, dynamicKeys) {
    if (dynamicKeys) {
      for (let i = 0; i < dynamicKeys.length; i++) dynamicProperty(props, dynamicKeys[i]);
    }
    const c = sample(() => Comp(props));
    return typeof c === "function" ? createMemo(c) : c;
  }

  function createActivityTracker() {
    let count = 0;
    const [read, trigger] = createSignal(false);
    return [read, () => count++ === 0 && trigger(true), () => --count <= 0 && trigger(false)];
  }
  const [active, increment, decrement] = createActivityTracker();

  const Types = {
    ATTRIBUTE: "attribute",
    PROPERTY: "property"
  },
        Attributes = {
    href: {
      type: Types.ATTRIBUTE
    },
    style: {
      type: Types.PROPERTY,
      alias: "style.cssText"
    },
    for: {
      type: Types.PROPERTY,
      alias: "htmlFor"
    },
    class: {
      type: Types.PROPERTY,
      alias: "className"
    },
    spellCheck: {
      type: Types.PROPERTY,
      alias: "spellcheck"
    },
    allowFullScreen: {
      type: Types.PROPERTY,
      alias: "allowFullscreen"
    },
    autoCapitalize: {
      type: Types.PROPERTY,
      alias: "autocapitalize"
    },
    autoFocus: {
      type: Types.PROPERTY,
      alias: "autofocus"
    },
    autoPlay: {
      type: Types.PROPERTY,
      alias: "autoplay"
    }
  },
        SVGAttributes = {
    className: {
      type: Types.ATTRIBUTE,
      alias: "class"
    },
    htmlFor: {
      type: Types.ATTRIBUTE,
      alias: "for"
    },
    tabIndex: {
      type: Types.ATTRIBUTE,
      alias: "tabindex"
    },
    allowReorder: {
      type: Types.ATTRIBUTE
    },
    attributeName: {
      type: Types.ATTRIBUTE
    },
    attributeType: {
      type: Types.ATTRIBUTE
    },
    autoReverse: {
      type: Types.ATTRIBUTE
    },
    baseFrequency: {
      type: Types.ATTRIBUTE
    },
    calcMode: {
      type: Types.ATTRIBUTE
    },
    clipPathUnits: {
      type: Types.ATTRIBUTE
    },
    contentScriptType: {
      type: Types.ATTRIBUTE
    },
    contentStyleType: {
      type: Types.ATTRIBUTE
    },
    diffuseConstant: {
      type: Types.ATTRIBUTE
    },
    edgeMode: {
      type: Types.ATTRIBUTE
    },
    externalResourcesRequired: {
      type: Types.ATTRIBUTE
    },
    filterRes: {
      type: Types.ATTRIBUTE
    },
    filterUnits: {
      type: Types.ATTRIBUTE
    },
    gradientTransform: {
      type: Types.ATTRIBUTE
    },
    gradientUnits: {
      type: Types.ATTRIBUTE
    },
    kernelMatrix: {
      type: Types.ATTRIBUTE
    },
    kernelUnitLength: {
      type: Types.ATTRIBUTE
    },
    keyPoints: {
      type: Types.ATTRIBUTE
    },
    keySplines: {
      type: Types.ATTRIBUTE
    },
    keyTimes: {
      type: Types.ATTRIBUTE
    },
    lengthAdjust: {
      type: Types.ATTRIBUTE
    },
    limitingConeAngle: {
      type: Types.ATTRIBUTE
    },
    markerHeight: {
      type: Types.ATTRIBUTE
    },
    markerUnits: {
      type: Types.ATTRIBUTE
    },
    maskContentUnits: {
      type: Types.ATTRIBUTE
    },
    maskUnits: {
      type: Types.ATTRIBUTE
    },
    numOctaves: {
      type: Types.ATTRIBUTE
    },
    pathLength: {
      type: Types.ATTRIBUTE
    },
    patternContentUnits: {
      type: Types.ATTRIBUTE
    },
    patternTransform: {
      type: Types.ATTRIBUTE
    },
    patternUnits: {
      type: Types.ATTRIBUTE
    },
    pointsAtX: {
      type: Types.ATTRIBUTE
    },
    pointsAtY: {
      type: Types.ATTRIBUTE
    },
    pointsAtZ: {
      type: Types.ATTRIBUTE
    },
    preserveAlpha: {
      type: Types.ATTRIBUTE
    },
    preserveAspectRatio: {
      type: Types.ATTRIBUTE
    },
    primitiveUnits: {
      type: Types.ATTRIBUTE
    },
    refX: {
      type: Types.ATTRIBUTE
    },
    refY: {
      type: Types.ATTRIBUTE
    },
    repeatCount: {
      type: Types.ATTRIBUTE
    },
    repeatDur: {
      type: Types.ATTRIBUTE
    },
    requiredExtensions: {
      type: Types.ATTRIBUTE
    },
    requiredFeatures: {
      type: Types.ATTRIBUTE
    },
    specularConstant: {
      type: Types.ATTRIBUTE
    },
    specularExponent: {
      type: Types.ATTRIBUTE
    },
    spreadMethod: {
      type: Types.ATTRIBUTE
    },
    startOffset: {
      type: Types.ATTRIBUTE
    },
    stdDeviation: {
      type: Types.ATTRIBUTE
    },
    stitchTiles: {
      type: Types.ATTRIBUTE
    },
    surfaceScale: {
      type: Types.ATTRIBUTE
    },
    systemLanguage: {
      type: Types.ATTRIBUTE
    },
    tableValues: {
      type: Types.ATTRIBUTE
    },
    targetX: {
      type: Types.ATTRIBUTE
    },
    targetY: {
      type: Types.ATTRIBUTE
    },
    textLength: {
      type: Types.ATTRIBUTE
    },
    viewBox: {
      type: Types.ATTRIBUTE
    },
    viewTarget: {
      type: Types.ATTRIBUTE
    },
    xChannelSelector: {
      type: Types.ATTRIBUTE
    },
    yChannelSelector: {
      type: Types.ATTRIBUTE
    },
    zoomAndPan: {
      type: Types.ATTRIBUTE
    }
  };
  const NonComposedEvents = new Set(["abort", "animationstart", "animationend", "animationiteration", "blur", "change", "copy", "cut", "error", "focus", "gotpointercapture", "load", "loadend", "loadstart", "lostpointercapture", "mouseenter", "mouseleave", "paste", "progress", "reset", "scroll", "select", "submit", "transitionstart", "transitioncancel", "transitionend", "transitionrun"]);

  function memo(fn, equal) {
    return createMemo(fn, undefined, equal);
  }

  function reconcileArrays(parentNode, a, b) {
    let bLength = b.length,
        aEnd = a.length,
        bEnd = bLength,
        aStart = 0,
        bStart = 0,
        after = a[aEnd - 1].nextSibling,
        map = null;
    while (aStart < aEnd || bStart < bEnd) {
      if (aEnd === aStart) {
        const node = bEnd < bLength ? bStart ? b[bStart - 1].nextSibling : b[bEnd - bStart] : after;
        while (bStart < bEnd) parentNode.insertBefore(b[bStart++], node);
      } else if (bEnd === bStart) {
        while (aStart < aEnd) {
          if (!map || !map.has(a[aStart])) parentNode.removeChild(a[aStart]);
          aStart++;
        }
      } else if (a[aStart] === b[bStart]) {
        aStart++;
        bStart++;
      } else if (a[aEnd - 1] === b[bEnd - 1]) {
        aEnd--;
        bEnd--;
      } else if (aEnd - aStart === 1 && bEnd - bStart === 1) {
        if (map && map.has(a[aStart]) || a[aStart].parentNode !== parentNode) {
          parentNode.insertBefore(b[bStart], bEnd < bLength ? b[bEnd] : after);
        } else parentNode.replaceChild(b[bStart], a[aStart]);
        break;
      } else if (a[aStart] === b[bEnd - 1] && b[bStart] === a[aEnd - 1]) {
        const node = a[--aEnd].nextSibling;
        parentNode.insertBefore(b[bStart++], a[aStart++].nextSibling);
        parentNode.insertBefore(b[--bEnd], node);
        a[aEnd] = b[bEnd];
      } else {
        if (!map) {
          map = new Map();
          let i = bStart;
          while (i < bEnd) map.set(b[i], i++);
        }
        if (map.has(a[aStart])) {
          const index = map.get(a[aStart]);
          if (bStart < index && index < bEnd) {
            let i = aStart,
                sequence = 1;
            while (++i < aEnd && i < bEnd) {
              if (!map.has(a[i]) || map.get(a[i]) !== index + sequence) break;
              sequence++;
            }
            if (sequence > index - bStart) {
              const node = a[aStart];
              while (bStart < index) parentNode.insertBefore(b[bStart++], node);
            } else parentNode.replaceChild(b[bStart++], a[aStart++]);
          } else aStart++;
        } else parentNode.removeChild(a[aStart++]);
      }
    }
  }

  const eventRegistry = new Set(),
        hydration = globalThis._$HYDRATION || (globalThis._$HYDRATION = {});
  function template(html, check, isSVG) {
    const t = document.createElement("template");
    t.innerHTML = html;
    if (check && t.innerHTML.split("<").length - 1 !== check) throw `Template html does not match input:\n${t.innerHTML}\n\n${html}`;
    let node = t.content.firstChild;
    if (isSVG) node = node.firstChild;
    return node;
  }
  function delegateEvents(eventNames) {
    for (let i = 0, l = eventNames.length; i < l; i++) {
      const name = eventNames[i];
      if (!eventRegistry.has(name)) {
        eventRegistry.add(name);
        document.addEventListener(name, eventHandler);
      }
    }
  }
  function setAttribute(node, name, value) {
    if (value === false || value == null) node.removeAttribute(name);else node.setAttribute(name, value);
  }
  function setAttributeNS(node, namespace, name, value) {
    if (value === false || value == null) node.removeAttributeNS(namespace, name);else node.setAttributeNS(namespace, name, value);
  }
  function classList(node, value, prev) {
    const classKeys = Object.keys(value);
    for (let i = 0, len = classKeys.length; i < len; i++) {
      const key = classKeys[i],
            classValue = !!value[key],
            classNames = key.split(/\s+/);
      if (!key || prev && prev[key] === classValue) continue;
      for (let j = 0, nameLen = classNames.length; j < nameLen; j++) node.classList.toggle(classNames[j], classValue);
    }
    return value;
  }
  function style(node, value, prev) {
    const nodeStyle = node.style;
    if (typeof value === "string") return nodeStyle.cssText = value;
    let v, s;
    if (prev != null && typeof prev !== "string") {
      for (s in value) {
        v = value[s];
        v !== prev[s] && nodeStyle.setProperty(s, v);
      }
      for (s in prev) {
        value[s] == null && nodeStyle.removeProperty(s);
      }
    } else {
      for (s in value) nodeStyle.setProperty(s, value[s]);
    }
    return value;
  }
  function spread(node, accessor, isSVG, skipChildren) {
    if (typeof accessor === "function") {
      createEffect(current => spreadExpression(node, accessor(), current, isSVG, skipChildren));
    } else spreadExpression(node, accessor, undefined, isSVG, skipChildren);
  }
  function insert(parent, accessor, marker, initial) {
    if (marker !== undefined && !initial) initial = [];
    if (typeof accessor !== "function") return insertExpression(parent, accessor, initial, marker);
    createEffect(current => insertExpression(parent, accessor(), current, marker), initial);
  }
  function assign(node, props, isSVG, skipChildren, prevProps = {}) {
    let info;
    for (const prop in props) {
      if (prop === "children") {
        if (!skipChildren) insertExpression(node, props.children);
        continue;
      }
      const value = props[prop];
      if (value === prevProps[prop]) continue;
      if (prop === "style") {
        style(node, value, prevProps[prop]);
      } else if (prop === "classList") {
        classList(node, value, prevProps[prop]);
      } else if (prop === "ref") {
        value(node);
      } else if (prop === "on") {
        for (const eventName in value) node.addEventListener(eventName, value[eventName]);
      } else if (prop === "onCapture") {
        for (const eventName in value) node.addEventListener(eventName, value[eventName], true);
      } else if (prop.slice(0, 2) === "on") {
        const lc = prop.toLowerCase();
        if (!NonComposedEvents.has(lc.slice(2))) {
          const name = lc.slice(2);
          if (Array.isArray(value)) {
            node[`__${name}`] = value[0];
            node[`__${name}Data`] = value[1];
          } else node[`__${name}`] = value;
          delegateEvents([name]);
        } else node[lc] = value;
      } else if (info = Attributes[prop]) {
        if (info.type === "attribute") {
          setAttribute(node, prop, value);
        } else node[info.alias] = value;
      } else if (isSVG || prop.indexOf("-") > -1 || prop.indexOf(":") > -1) {
        const ns = prop.indexOf(":") > -1 && SVGNamepace[prop.split(":")[0]];
        if (ns) setAttributeNS(node, ns, prop, value);else if (info = SVGAttributes[prop]) {
          if (info.alias) setAttribute(node, info.alias, value);else setAttribute(node, prop, value);
        } else setAttribute(node, prop.replace(/([A-Z])/g, g => `-${g[0].toLowerCase()}`), value);
      } else node[prop] = value;
      prevProps[prop] = value;
    }
  }
  function eventHandler(e) {
    const key = `__${e.type}`;
    let node = e.composedPath && e.composedPath()[0] || e.target;
    if (e.target !== node) {
      Object.defineProperty(e, "target", {
        configurable: true,
        value: node
      });
    }
    Object.defineProperty(e, "currentTarget", {
      configurable: true,
      get() {
        return node;
      }
    });
    while (node !== null) {
      const handler = node[key];
      if (handler) {
        const data = node[`${key}Data`];
        data ? handler(data, e) : handler(e);
        if (e.cancelBubble) return;
      }
      node = node.host && node.host instanceof Node ? node.host : node.parentNode;
    }
  }
  function spreadExpression(node, props, prevProps = {}, isSVG, skipChildren) {
    if (!skipChildren && "children" in props) {
      createEffect(() => prevProps.children = insertExpression(node, props.children, prevProps.children));
    }
    createEffect(() => assign(node, props, isSVG, true, prevProps));
    return prevProps;
  }
  function insertExpression(parent, value, current, marker, unwrapArray) {
    while (typeof current === "function") current = current();
    if (value === current) return current;
    const t = typeof value,
          multi = marker !== undefined;
    parent = multi && current[0] && current[0].parentNode || parent;
    if (t === "string" || t === "number") {
      if (t === "number") value = value.toString();
      if (multi) {
        let node = current[0];
        if (node && node.nodeType === 3) {
          node.data = value;
        } else node = document.createTextNode(value);
        current = cleanChildren(parent, current, marker, node);
      } else {
        if (current !== "" && typeof current === "string") {
          current = parent.firstChild.data = value;
        } else current = parent.textContent = value;
      }
    } else if (value == null || t === "boolean") {
      if (hydration.context && hydration.context.registry) return current;
      current = cleanChildren(parent, current, marker);
    } else if (t === "function") {
      createEffect(() => current = insertExpression(parent, value(), current, marker));
      return () => current;
    } else if (Array.isArray(value)) {
      const array = [];
      if (normalizeIncomingArray(array, value, unwrapArray)) {
        createEffect(() => current = insertExpression(parent, array, current, marker, true));
        return () => current;
      }
      if (hydration.context && hydration.context.registry) return array;
      if (array.length === 0) {
        current = cleanChildren(parent, current, marker);
        if (multi) return current;
      } else {
        if (Array.isArray(current)) {
          if (current.length === 0) {
            appendNodes(parent, array, marker);
          } else reconcileArrays(parent, current, array);
        } else if (current == null || current === "") {
          appendNodes(parent, array);
        } else {
          reconcileArrays(parent, multi && current || [parent.firstChild], array);
        }
      }
      current = array;
    } else if (value instanceof Node) {
      if (Array.isArray(current)) {
        if (multi) return current = cleanChildren(parent, current, marker, value);
        cleanChildren(parent, current, null, value);
      } else if (current == null || current === "" || !parent.firstChild) {
        parent.appendChild(value);
      } else parent.replaceChild(value, parent.firstChild);
      current = value;
    } else console.warn(`Skipped inserting`, value);
    return current;
  }
  function normalizeIncomingArray(normalized, array, unwrap) {
    let dynamic = false;
    for (let i = 0, len = array.length; i < len; i++) {
      let item = array[i],
          t;
      if (item instanceof Node) {
        normalized.push(item);
      } else if (item == null || item === true || item === false) ; else if (Array.isArray(item)) {
        dynamic = normalizeIncomingArray(normalized, item) || dynamic;
      } else if ((t = typeof item) === "string") {
        normalized.push(document.createTextNode(item));
      } else if (t === "function") {
        if (unwrap) {
          const idx = item();
          dynamic = normalizeIncomingArray(normalized, Array.isArray(idx) ? idx : [idx]) || dynamic;
        } else {
          normalized.push(item);
          dynamic = true;
        }
      } else normalized.push(document.createTextNode(item.toString()));
    }
    return dynamic;
  }
  function appendNodes(parent, array, marker) {
    for (let i = 0, len = array.length; i < len; i++) parent.insertBefore(array[i], marker);
  }
  function cleanChildren(parent, current, marker, replacement) {
    if (marker === undefined) return parent.textContent = "";
    const node = replacement || document.createTextNode("");
    if (current.length) {
      let inserted = false;
      for (let i = current.length - 1; i >= 0; i--) {
        const el = current[i];
        if (node !== el) {
          const isParent = el.parentNode === parent;
          if (!inserted && !i) isParent ? parent.replaceChild(node, el) : parent.insertBefore(node, marker);else isParent && parent.removeChild(el);
        } else inserted = true;
      }
    } else parent.insertBefore(node, marker);
    return [node];
  }

  function cloneProps(props) {
    const propKeys = Object.keys(props);
    return propKeys.reduce((memo, k) => {
      const prop = props[k];
      memo[k] = Object.assign({}, prop);
      if (isObject(prop.value) && !isFunction(prop.value) && !Array.isArray(prop.value)) memo[k].value = Object.assign({}, prop.value);
      if (Array.isArray(prop.value)) memo[k].value = prop.value.slice(0);
      return memo;
    }, {});
  }

  function normalizePropDefs(props) {
    if (!props) return {};
    const propKeys = Object.keys(props);
    return propKeys.reduce((memo, k) => {
      const v = props[k];
      memo[k] = !(isObject(v) && "value" in v) ? {
        value: v
      } : v;
      memo[k].attribute || (memo[k].attribute = toAttribute(k));
      return memo;
    }, {});
  }
  function propValues(props) {
    const propKeys = Object.keys(props);
    return propKeys.reduce((memo, k) => {
      memo[k] = props[k].value;
      return memo;
    }, {});
  }
  function initializeProps(element, propDefinition) {
    const props = cloneProps(propDefinition),
          propKeys = Object.keys(propDefinition);
    propKeys.forEach(key => {
      const prop = props[key],
            attr = element.getAttribute(prop.attribute),
            value = element[key];
      if (attr) prop.value = parseAttributeValue(attr);
      if (value != null) prop.value = Array.isArray(value) ? value.slice(0) : value;
      reflect(element, prop.attribute, prop.value);
      Object.defineProperty(element, key, {
        get() {
          return prop.value;
        },

        set(val) {
          const oldValue = prop.value;
          prop.value = val;
          reflect(this, prop.attribute, prop.value);

          for (let i = 0, l = this.__propertyChangedCallbacks.length; i < l; i++) {
            this.__propertyChangedCallbacks[i](key, val, oldValue);
          }
        },

        enumerable: true,
        configurable: true
      });
    });
    return props;
  }
  function parseAttributeValue(value) {
    if (!value) return;
    let parsed;

    try {
      parsed = JSON.parse(value);
    } catch (err) {
      parsed = value;
    }

    if (!(typeof parsed === "string")) return parsed;
    if (/^[0-9]*$/.test(parsed)) return +parsed;
    return parsed;
  }
  function reflect(node, attribute, value) {
    if (isObject(value)) return;
    let reflect = value ? typeof value.toString === "function" ? value.toString() : undefined : undefined;

    if (reflect && reflect !== "false") {
      node.__updating[attribute] = true;
      if (reflect === "true") reflect = "";
      node.setAttribute(attribute, reflect);
      Promise.resolve().then(() => delete node.__updating[attribute]);
    } else node.removeAttribute(attribute);
  }
  function toAttribute(propName) {
    return propName.replace(/\.?([A-Z]+)/g, (x, y) => "-" + y.toLowerCase()).replace("_", "-").replace(/^-/, "");
  }
  function isObject(obj) {
    return obj != null && (typeof obj === "object" || typeof obj === "function");
  }
  function isFunction(val) {
    return Object.prototype.toString.call(val) === "[object Function]";
  }
  function isConstructor(f) {
    return typeof f === "function" && f.toString().indexOf("class") === 0;
  }

  let currentElement;
  function noShadowDOM() {
    Object.defineProperty(currentElement, "renderRoot", {
      value: currentElement
    });
  }
  function createElementType(BaseElement, propDefinition) {
    const propKeys = Object.keys(propDefinition);
    return class CustomElement extends BaseElement {
      static get observedAttributes() {
        return propKeys.map(k => propDefinition[k].attribute);
      }

      constructor() {
        super();
        this.__initialized = false;
        this.__released = false;
        this.__releaseCallbacks = [];
        this.__propertyChangedCallbacks = [];
        this.__updating = {};
        this.props = {};
      }

      connectedCallback() {
        // check that infact it connected since polyfill sometimes double calls
        if (!this.isConnected || this.__initialized) return;
        this.__releaseCallbacks = [];
        this.__propertyChangedCallbacks = [];
        this.__updating = {};
        this.props = initializeProps(this, propDefinition);
        const props = propValues(this.props),
              ComponentType = this.Component,
              outerElement = currentElement;

        try {
          currentElement = this;
          this.__initialized = true;
          if (isConstructor(ComponentType)) new ComponentType(props, {
            element: this
          });else ComponentType(props, {
            element: this
          });
        } finally {
          currentElement = outerElement;
        }
      }

      async disconnectedCallback() {
        // prevent premature releasing when element is only temporarely removed from DOM
        await Promise.resolve();
        if (this.isConnected) return;
        this.__propertyChangedCallbacks.length = 0;
        let callback = null;

        while (callback = this.__releaseCallbacks.pop()) callback(this);

        delete this.__initialized;
        this.__released = true;
      }

      attributeChangedCallback(name, oldVal, newVal) {
        if (!this.__initialized) return;
        if (this.__updating[name]) return;
        name = this.lookupProp(name);

        if (name in propDefinition) {
          if (newVal == null && !this[name]) return;
          this[name] = parseAttributeValue(newVal);
        }
      }

      lookupProp(attrName) {
        if (!propDefinition) return;
        return propKeys.find(k => attrName === k || attrName === propDefinition[k].attribute);
      }

      get renderRoot() {
        return this.shadowRoot || this.attachShadow({
          mode: "open"
        });
      }

      addReleaseCallback(fn) {
        this.__releaseCallbacks.push(fn);
      }

      addPropertyChangedCallback(fn) {
        this.__propertyChangedCallbacks.push(fn);
      }

    };
  }

  function register(tag, props = {}, options = {}) {
    const {
      BaseElement = HTMLElement,
      extension
    } = options;
    return ComponentType => {
      if (!tag) throw new Error("tag is required to register a Component");
      let ElementType = customElements.get(tag);

      if (ElementType) {
        // Consider disabling this in a production mode
        ElementType.prototype.Component = ComponentType;
        return ElementType;
      }

      ElementType = createElementType(BaseElement, normalizePropDefs(props));
      ElementType.prototype.Component = ComponentType;
      ElementType.prototype.registeredTag = tag;
      customElements.define(tag, ElementType, extension);
      return ElementType;
    };
  }

  function withSolid(ComponentType) {
    return (rawProps, options) => {
      const {
        element
      } = options;
      return createRoot(dispose => {
        const [props, setProps] = createState(rawProps);
        element.addPropertyChangedCallback((key, val) => setProps({
          [key]: val
        }));
        element.addReleaseCallback(() => dispose());
        const comp = ComponentType(props, options);
        return insert(element.renderRoot, comp);
      }, element.assignedSlot && element.assignedSlot._context || element._context);
    };
  }

  function customElement(tag, props, ComponentType) {
    if (arguments.length === 2) {
      ComponentType = props;
      props = {};
    }

    return register(tag, props)(withSolid(ComponentType));
  }

  /*! *****************************************************************************
  Copyright (c) Microsoft Corporation.

  Permission to use, copy, modify, and/or distribute this software for any
  purpose with or without fee is hereby granted.

  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
  REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
  AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
  INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
  LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
  OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
  PERFORMANCE OF THIS SOFTWARE.
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

  function __read(o, n) {
      var m = typeof Symbol === "function" && o[Symbol.iterator];
      if (!m) return o;
      var i = m.call(o), r, ar = [], e;
      try {
          while ((n === void 0 || n-- > 0) && !(r = i.next()).done) ar.push(r.value);
      }
      catch (error) { e = { error: error }; }
      finally {
          try {
              if (r && !r.done && (m = i["return"])) m.call(i);
          }
          finally { if (e) throw e.error; }
      }
      return ar;
  }

  function __spread() {
      for (var ar = [], i = 0; i < arguments.length; i++)
          ar = ar.concat(__read(arguments[i]));
      return ar;
  }

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var jsEventTypeMap = {
      animationend: {
          cssProperty: 'animation',
          prefixed: 'webkitAnimationEnd',
          standard: 'animationend',
      },
      animationiteration: {
          cssProperty: 'animation',
          prefixed: 'webkitAnimationIteration',
          standard: 'animationiteration',
      },
      animationstart: {
          cssProperty: 'animation',
          prefixed: 'webkitAnimationStart',
          standard: 'animationstart',
      },
      transitionend: {
          cssProperty: 'transition',
          prefixed: 'webkitTransitionEnd',
          standard: 'transitionend',
      },
  };
  function isWindow(windowObj) {
      return Boolean(windowObj.document) && typeof windowObj.document.createElement === 'function';
  }
  function getCorrectEventName(windowObj, eventType) {
      if (isWindow(windowObj) && eventType in jsEventTypeMap) {
          var el = windowObj.document.createElement('div');
          var _a = jsEventTypeMap[eventType], standard = _a.standard, prefixed = _a.prefixed, cssProperty = _a.cssProperty;
          var isStandard = cssProperty in el.style;
          return isStandard ? standard : prefixed;
      }
      return eventType;
  }

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCFoundation = /** @class */ (function () {
      function MDCFoundation(adapter) {
          if (adapter === void 0) { adapter = {}; }
          this.adapter = adapter;
      }
      Object.defineProperty(MDCFoundation, "cssClasses", {
          get: function () {
              // Classes extending MDCFoundation should implement this method to return an object which exports every
              // CSS class the foundation class needs as a property. e.g. {ACTIVE: 'mdc-component--active'}
              return {};
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCFoundation, "strings", {
          get: function () {
              // Classes extending MDCFoundation should implement this method to return an object which exports all
              // semantic strings as constants. e.g. {ARIA_ROLE: 'tablist'}
              return {};
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCFoundation, "numbers", {
          get: function () {
              // Classes extending MDCFoundation should implement this method to return an object which exports all
              // of its semantic numbers as constants. e.g. {ANIMATION_DELAY_MS: 350}
              return {};
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCFoundation, "defaultAdapter", {
          get: function () {
              // Classes extending MDCFoundation may choose to implement this getter in order to provide a convenient
              // way of viewing the necessary methods of an adapter. In the future, this could also be used for adapter
              // validation.
              return {};
          },
          enumerable: true,
          configurable: true
      });
      MDCFoundation.prototype.init = function () {
          // Subclasses should override this method to perform initialization routines (registering events, etc.)
      };
      MDCFoundation.prototype.destroy = function () {
          // Subclasses should override this method to perform de-initialization routines (de-registering events, etc.)
      };
      return MDCFoundation;
  }());

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCComponent = /** @class */ (function () {
      function MDCComponent(root, foundation) {
          var args = [];
          for (var _i = 2; _i < arguments.length; _i++) {
              args[_i - 2] = arguments[_i];
          }
          this.root = root;
          this.initialize.apply(this, __spread(args));
          // Note that we initialize foundation here and not within the constructor's default param so that
          // this.root_ is defined and can be used within the foundation class.
          this.foundation =
              foundation === undefined ? this.getDefaultFoundation() : foundation;
          this.foundation.init();
          this.initialSyncWithDOM();
      }
      MDCComponent.attachTo = function (root) {
          // Subclasses which extend MDCBase should provide an attachTo() method that takes a root element and
          // returns an instantiated component with its root set to that element. Also note that in the cases of
          // subclasses, an explicit foundation class will not have to be passed in; it will simply be initialized
          // from getDefaultFoundation().
          return new MDCComponent(root, new MDCFoundation({}));
      };
      /* istanbul ignore next: method param only exists for typing purposes; it does not need to be unit tested */
      MDCComponent.prototype.initialize = function () {
          var _args = [];
          for (var _i = 0; _i < arguments.length; _i++) {
              _args[_i] = arguments[_i];
          }
          // Subclasses can override this to do any additional setup work that would be considered part of a
          // "constructor". Essentially, it is a hook into the parent constructor before the foundation is
          // initialized. Any additional arguments besides root and foundation will be passed in here.
      };
      MDCComponent.prototype.getDefaultFoundation = function () {
          // Subclasses must override this method to return a properly configured foundation class for the
          // component.
          throw new Error('Subclasses must override getDefaultFoundation to return a properly configured ' +
              'foundation class');
      };
      MDCComponent.prototype.initialSyncWithDOM = function () {
          // Subclasses should override this method if they need to perform work to synchronize with a host DOM
          // object. An example of this would be a form control wrapper that needs to synchronize its internal state
          // to some property or attribute of the host DOM. Please note: this is *not* the place to perform DOM
          // reads/writes that would cause layout / paint, as this is called synchronously from within the constructor.
      };
      MDCComponent.prototype.destroy = function () {
          // Subclasses may implement this method to release any resources / deregister any listeners they have
          // attached. An example of this might be deregistering a resize event from the window object.
          this.foundation.destroy();
      };
      MDCComponent.prototype.listen = function (evtType, handler, options) {
          this.root.addEventListener(evtType, handler, options);
      };
      MDCComponent.prototype.unlisten = function (evtType, handler, options) {
          this.root.removeEventListener(evtType, handler, options);
      };
      /**
       * Fires a cross-browser-compatible custom event from the component root of the given type, with the given data.
       */
      MDCComponent.prototype.emit = function (evtType, evtData, shouldBubble) {
          if (shouldBubble === void 0) { shouldBubble = false; }
          var evt;
          if (typeof CustomEvent === 'function') {
              evt = new CustomEvent(evtType, {
                  bubbles: shouldBubble,
                  detail: evtData,
              });
          }
          else {
              evt = document.createEvent('CustomEvent');
              evt.initCustomEvent(evtType, shouldBubble, false, evtData);
          }
          this.root.dispatchEvent(evt);
      };
      return MDCComponent;
  }());

  /**
   * @license
   * Copyright 2019 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  /**
   * Determine whether the current browser supports passive event listeners, and
   * if so, use them.
   */
  function applyPassive(globalObj) {
      if (globalObj === void 0) { globalObj = window; }
      return supportsPassiveOption(globalObj) ?
          { passive: true } :
          false;
  }
  function supportsPassiveOption(globalObj) {
      if (globalObj === void 0) { globalObj = window; }
      // See
      // https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
      var passiveSupported = false;
      try {
          var options = {
              // This function will be called when the browser
              // attempts to access the passive property.
              get passive() {
                  passiveSupported = true;
                  return false;
              }
          };
          var handler = function () { };
          globalObj.document.addEventListener('test', handler, options);
          globalObj.document.removeEventListener('test', handler, options);
      }
      catch (err) {
          passiveSupported = false;
      }
      return passiveSupported;
  }

  /**
   * @license
   * Copyright 2018 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  function matches(element, selector) {
      var nativeMatches = element.matches
          || element.webkitMatchesSelector
          || element.msMatchesSelector;
      return nativeMatches.call(element, selector);
  }
  /**
   * Used to compute the estimated scroll width of elements. When an element is
   * hidden due to display: none; being applied to a parent element, the width is
   * returned as 0. However, the element will have a true width once no longer
   * inside a display: none context. This method computes an estimated width when
   * the element is hidden or returns the true width when the element is visble.
   * @param {Element} element the element whose width to estimate
   */
  function estimateScrollWidth(element) {
      // Check the offsetParent. If the element inherits display: none from any
      // parent, the offsetParent property will be null (see
      // https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/offsetParent).
      // This check ensures we only clone the node when necessary.
      var htmlEl = element;
      if (htmlEl.offsetParent !== null) {
          return htmlEl.scrollWidth;
      }
      var clone = htmlEl.cloneNode(true);
      clone.style.setProperty('position', 'absolute');
      clone.style.setProperty('transform', 'translate(-9999px, -9999px)');
      document.documentElement.appendChild(clone);
      var scrollWidth = clone.scrollWidth;
      document.documentElement.removeChild(clone);
      return scrollWidth;
  }

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses = {
      // Ripple is a special case where the "root" component is really a "mixin" of sorts,
      // given that it's an 'upgrade' to an existing component. That being said it is the root
      // CSS class that all other CSS classes derive from.
      BG_FOCUSED: 'mdc-ripple-upgraded--background-focused',
      FG_ACTIVATION: 'mdc-ripple-upgraded--foreground-activation',
      FG_DEACTIVATION: 'mdc-ripple-upgraded--foreground-deactivation',
      ROOT: 'mdc-ripple-upgraded',
      UNBOUNDED: 'mdc-ripple-upgraded--unbounded',
  };
  var strings = {
      VAR_FG_SCALE: '--mdc-ripple-fg-scale',
      VAR_FG_SIZE: '--mdc-ripple-fg-size',
      VAR_FG_TRANSLATE_END: '--mdc-ripple-fg-translate-end',
      VAR_FG_TRANSLATE_START: '--mdc-ripple-fg-translate-start',
      VAR_LEFT: '--mdc-ripple-left',
      VAR_TOP: '--mdc-ripple-top',
  };
  var numbers = {
      DEACTIVATION_TIMEOUT_MS: 225,
      FG_DEACTIVATION_MS: 150,
      INITIAL_ORIGIN_SCALE: 0.6,
      PADDING: 10,
      TAP_DELAY_MS: 300,
  };

  /**
   * Stores result from supportsCssVariables to avoid redundant processing to
   * detect CSS custom variable support.
   */
  var supportsCssVariables_;
  function supportsCssVariables(windowObj, forceRefresh) {
      if (forceRefresh === void 0) { forceRefresh = false; }
      var CSS = windowObj.CSS;
      var supportsCssVars = supportsCssVariables_;
      if (typeof supportsCssVariables_ === 'boolean' && !forceRefresh) {
          return supportsCssVariables_;
      }
      var supportsFunctionPresent = CSS && typeof CSS.supports === 'function';
      if (!supportsFunctionPresent) {
          return false;
      }
      var explicitlySupportsCssVars = CSS.supports('--css-vars', 'yes');
      // See: https://bugs.webkit.org/show_bug.cgi?id=154669
      // See: README section on Safari
      var weAreFeatureDetectingSafari10plus = (CSS.supports('(--css-vars: yes)') &&
          CSS.supports('color', '#00000000'));
      supportsCssVars =
          explicitlySupportsCssVars || weAreFeatureDetectingSafari10plus;
      if (!forceRefresh) {
          supportsCssVariables_ = supportsCssVars;
      }
      return supportsCssVars;
  }
  function getNormalizedEventCoords(evt, pageOffset, clientRect) {
      if (!evt) {
          return { x: 0, y: 0 };
      }
      var x = pageOffset.x, y = pageOffset.y;
      var documentX = x + clientRect.left;
      var documentY = y + clientRect.top;
      var normalizedX;
      var normalizedY;
      // Determine touch point relative to the ripple container.
      if (evt.type === 'touchstart') {
          var touchEvent = evt;
          normalizedX = touchEvent.changedTouches[0].pageX - documentX;
          normalizedY = touchEvent.changedTouches[0].pageY - documentY;
      }
      else {
          var mouseEvent = evt;
          normalizedX = mouseEvent.pageX - documentX;
          normalizedY = mouseEvent.pageY - documentY;
      }
      return { x: normalizedX, y: normalizedY };
  }

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  // Activation events registered on the root element of each instance for activation
  var ACTIVATION_EVENT_TYPES = [
      'touchstart', 'pointerdown', 'mousedown', 'keydown',
  ];
  // Deactivation events registered on documentElement when a pointer-related down event occurs
  var POINTER_DEACTIVATION_EVENT_TYPES = [
      'touchend', 'pointerup', 'mouseup', 'contextmenu',
  ];
  // simultaneous nested activations
  var activatedTargets = [];
  var MDCRippleFoundation = /** @class */ (function (_super) {
      __extends(MDCRippleFoundation, _super);
      function MDCRippleFoundation(adapter) {
          var _this = _super.call(this, __assign(__assign({}, MDCRippleFoundation.defaultAdapter), adapter)) || this;
          _this.activationAnimationHasEnded_ = false;
          _this.activationTimer_ = 0;
          _this.fgDeactivationRemovalTimer_ = 0;
          _this.fgScale_ = '0';
          _this.frame_ = { width: 0, height: 0 };
          _this.initialSize_ = 0;
          _this.layoutFrame_ = 0;
          _this.maxRadius_ = 0;
          _this.unboundedCoords_ = { left: 0, top: 0 };
          _this.activationState_ = _this.defaultActivationState_();
          _this.activationTimerCallback_ = function () {
              _this.activationAnimationHasEnded_ = true;
              _this.runDeactivationUXLogicIfReady_();
          };
          _this.activateHandler_ = function (e) { return _this.activate_(e); };
          _this.deactivateHandler_ = function () { return _this.deactivate_(); };
          _this.focusHandler_ = function () { return _this.handleFocus(); };
          _this.blurHandler_ = function () { return _this.handleBlur(); };
          _this.resizeHandler_ = function () { return _this.layout(); };
          return _this;
      }
      Object.defineProperty(MDCRippleFoundation, "cssClasses", {
          get: function () {
              return cssClasses;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCRippleFoundation, "strings", {
          get: function () {
              return strings;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCRippleFoundation, "numbers", {
          get: function () {
              return numbers;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCRippleFoundation, "defaultAdapter", {
          get: function () {
              return {
                  addClass: function () { return undefined; },
                  browserSupportsCssVars: function () { return true; },
                  computeBoundingRect: function () { return ({ top: 0, right: 0, bottom: 0, left: 0, width: 0, height: 0 }); },
                  containsEventTarget: function () { return true; },
                  deregisterDocumentInteractionHandler: function () { return undefined; },
                  deregisterInteractionHandler: function () { return undefined; },
                  deregisterResizeHandler: function () { return undefined; },
                  getWindowPageOffset: function () { return ({ x: 0, y: 0 }); },
                  isSurfaceActive: function () { return true; },
                  isSurfaceDisabled: function () { return true; },
                  isUnbounded: function () { return true; },
                  registerDocumentInteractionHandler: function () { return undefined; },
                  registerInteractionHandler: function () { return undefined; },
                  registerResizeHandler: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  updateCssVariable: function () { return undefined; },
              };
          },
          enumerable: true,
          configurable: true
      });
      MDCRippleFoundation.prototype.init = function () {
          var _this = this;
          var supportsPressRipple = this.supportsPressRipple_();
          this.registerRootHandlers_(supportsPressRipple);
          if (supportsPressRipple) {
              var _a = MDCRippleFoundation.cssClasses, ROOT_1 = _a.ROOT, UNBOUNDED_1 = _a.UNBOUNDED;
              requestAnimationFrame(function () {
                  _this.adapter.addClass(ROOT_1);
                  if (_this.adapter.isUnbounded()) {
                      _this.adapter.addClass(UNBOUNDED_1);
                      // Unbounded ripples need layout logic applied immediately to set coordinates for both shade and ripple
                      _this.layoutInternal_();
                  }
              });
          }
      };
      MDCRippleFoundation.prototype.destroy = function () {
          var _this = this;
          if (this.supportsPressRipple_()) {
              if (this.activationTimer_) {
                  clearTimeout(this.activationTimer_);
                  this.activationTimer_ = 0;
                  this.adapter.removeClass(MDCRippleFoundation.cssClasses.FG_ACTIVATION);
              }
              if (this.fgDeactivationRemovalTimer_) {
                  clearTimeout(this.fgDeactivationRemovalTimer_);
                  this.fgDeactivationRemovalTimer_ = 0;
                  this.adapter.removeClass(MDCRippleFoundation.cssClasses.FG_DEACTIVATION);
              }
              var _a = MDCRippleFoundation.cssClasses, ROOT_2 = _a.ROOT, UNBOUNDED_2 = _a.UNBOUNDED;
              requestAnimationFrame(function () {
                  _this.adapter.removeClass(ROOT_2);
                  _this.adapter.removeClass(UNBOUNDED_2);
                  _this.removeCssVars_();
              });
          }
          this.deregisterRootHandlers_();
          this.deregisterDeactivationHandlers_();
      };
      /**
       * @param evt Optional event containing position information.
       */
      MDCRippleFoundation.prototype.activate = function (evt) {
          this.activate_(evt);
      };
      MDCRippleFoundation.prototype.deactivate = function () {
          this.deactivate_();
      };
      MDCRippleFoundation.prototype.layout = function () {
          var _this = this;
          if (this.layoutFrame_) {
              cancelAnimationFrame(this.layoutFrame_);
          }
          this.layoutFrame_ = requestAnimationFrame(function () {
              _this.layoutInternal_();
              _this.layoutFrame_ = 0;
          });
      };
      MDCRippleFoundation.prototype.setUnbounded = function (unbounded) {
          var UNBOUNDED = MDCRippleFoundation.cssClasses.UNBOUNDED;
          if (unbounded) {
              this.adapter.addClass(UNBOUNDED);
          }
          else {
              this.adapter.removeClass(UNBOUNDED);
          }
      };
      MDCRippleFoundation.prototype.handleFocus = function () {
          var _this = this;
          requestAnimationFrame(function () { return _this.adapter.addClass(MDCRippleFoundation.cssClasses.BG_FOCUSED); });
      };
      MDCRippleFoundation.prototype.handleBlur = function () {
          var _this = this;
          requestAnimationFrame(function () { return _this.adapter.removeClass(MDCRippleFoundation.cssClasses.BG_FOCUSED); });
      };
      /**
       * We compute this property so that we are not querying information about the client
       * until the point in time where the foundation requests it. This prevents scenarios where
       * client-side feature-detection may happen too early, such as when components are rendered on the server
       * and then initialized at mount time on the client.
       */
      MDCRippleFoundation.prototype.supportsPressRipple_ = function () {
          return this.adapter.browserSupportsCssVars();
      };
      MDCRippleFoundation.prototype.defaultActivationState_ = function () {
          return {
              activationEvent: undefined,
              hasDeactivationUXRun: false,
              isActivated: false,
              isProgrammatic: false,
              wasActivatedByPointer: false,
              wasElementMadeActive: false,
          };
      };
      /**
       * supportsPressRipple Passed from init to save a redundant function call
       */
      MDCRippleFoundation.prototype.registerRootHandlers_ = function (supportsPressRipple) {
          var _this = this;
          if (supportsPressRipple) {
              ACTIVATION_EVENT_TYPES.forEach(function (evtType) {
                  _this.adapter.registerInteractionHandler(evtType, _this.activateHandler_);
              });
              if (this.adapter.isUnbounded()) {
                  this.adapter.registerResizeHandler(this.resizeHandler_);
              }
          }
          this.adapter.registerInteractionHandler('focus', this.focusHandler_);
          this.adapter.registerInteractionHandler('blur', this.blurHandler_);
      };
      MDCRippleFoundation.prototype.registerDeactivationHandlers_ = function (evt) {
          var _this = this;
          if (evt.type === 'keydown') {
              this.adapter.registerInteractionHandler('keyup', this.deactivateHandler_);
          }
          else {
              POINTER_DEACTIVATION_EVENT_TYPES.forEach(function (evtType) {
                  _this.adapter.registerDocumentInteractionHandler(evtType, _this.deactivateHandler_);
              });
          }
      };
      MDCRippleFoundation.prototype.deregisterRootHandlers_ = function () {
          var _this = this;
          ACTIVATION_EVENT_TYPES.forEach(function (evtType) {
              _this.adapter.deregisterInteractionHandler(evtType, _this.activateHandler_);
          });
          this.adapter.deregisterInteractionHandler('focus', this.focusHandler_);
          this.adapter.deregisterInteractionHandler('blur', this.blurHandler_);
          if (this.adapter.isUnbounded()) {
              this.adapter.deregisterResizeHandler(this.resizeHandler_);
          }
      };
      MDCRippleFoundation.prototype.deregisterDeactivationHandlers_ = function () {
          var _this = this;
          this.adapter.deregisterInteractionHandler('keyup', this.deactivateHandler_);
          POINTER_DEACTIVATION_EVENT_TYPES.forEach(function (evtType) {
              _this.adapter.deregisterDocumentInteractionHandler(evtType, _this.deactivateHandler_);
          });
      };
      MDCRippleFoundation.prototype.removeCssVars_ = function () {
          var _this = this;
          var rippleStrings = MDCRippleFoundation.strings;
          var keys = Object.keys(rippleStrings);
          keys.forEach(function (key) {
              if (key.indexOf('VAR_') === 0) {
                  _this.adapter.updateCssVariable(rippleStrings[key], null);
              }
          });
      };
      MDCRippleFoundation.prototype.activate_ = function (evt) {
          var _this = this;
          if (this.adapter.isSurfaceDisabled()) {
              return;
          }
          var activationState = this.activationState_;
          if (activationState.isActivated) {
              return;
          }
          // Avoid reacting to follow-on events fired by touch device after an already-processed user interaction
          var previousActivationEvent = this.previousActivationEvent_;
          var isSameInteraction = previousActivationEvent && evt !== undefined && previousActivationEvent.type !== evt.type;
          if (isSameInteraction) {
              return;
          }
          activationState.isActivated = true;
          activationState.isProgrammatic = evt === undefined;
          activationState.activationEvent = evt;
          activationState.wasActivatedByPointer = activationState.isProgrammatic ? false : evt !== undefined && (evt.type === 'mousedown' || evt.type === 'touchstart' || evt.type === 'pointerdown');
          var hasActivatedChild = evt !== undefined &&
              activatedTargets.length > 0 &&
              activatedTargets.some(function (target) { return _this.adapter.containsEventTarget(target); });
          if (hasActivatedChild) {
              // Immediately reset activation state, while preserving logic that prevents touch follow-on events
              this.resetActivationState_();
              return;
          }
          if (evt !== undefined) {
              activatedTargets.push(evt.target);
              this.registerDeactivationHandlers_(evt);
          }
          activationState.wasElementMadeActive = this.checkElementMadeActive_(evt);
          if (activationState.wasElementMadeActive) {
              this.animateActivation_();
          }
          requestAnimationFrame(function () {
              // Reset array on next frame after the current event has had a chance to bubble to prevent ancestor ripples
              activatedTargets = [];
              if (!activationState.wasElementMadeActive
                  && evt !== undefined
                  && (evt.key === ' ' || evt.keyCode === 32)) {
                  // If space was pressed, try again within an rAF call to detect :active, because different UAs report
                  // active states inconsistently when they're called within event handling code:
                  // - https://bugs.chromium.org/p/chromium/issues/detail?id=635971
                  // - https://bugzilla.mozilla.org/show_bug.cgi?id=1293741
                  // We try first outside rAF to support Edge, which does not exhibit this problem, but will crash if a CSS
                  // variable is set within a rAF callback for a submit button interaction (#2241).
                  activationState.wasElementMadeActive = _this.checkElementMadeActive_(evt);
                  if (activationState.wasElementMadeActive) {
                      _this.animateActivation_();
                  }
              }
              if (!activationState.wasElementMadeActive) {
                  // Reset activation state immediately if element was not made active.
                  _this.activationState_ = _this.defaultActivationState_();
              }
          });
      };
      MDCRippleFoundation.prototype.checkElementMadeActive_ = function (evt) {
          return (evt !== undefined && evt.type === 'keydown') ?
              this.adapter.isSurfaceActive() :
              true;
      };
      MDCRippleFoundation.prototype.animateActivation_ = function () {
          var _this = this;
          var _a = MDCRippleFoundation.strings, VAR_FG_TRANSLATE_START = _a.VAR_FG_TRANSLATE_START, VAR_FG_TRANSLATE_END = _a.VAR_FG_TRANSLATE_END;
          var _b = MDCRippleFoundation.cssClasses, FG_DEACTIVATION = _b.FG_DEACTIVATION, FG_ACTIVATION = _b.FG_ACTIVATION;
          var DEACTIVATION_TIMEOUT_MS = MDCRippleFoundation.numbers.DEACTIVATION_TIMEOUT_MS;
          this.layoutInternal_();
          var translateStart = '';
          var translateEnd = '';
          if (!this.adapter.isUnbounded()) {
              var _c = this.getFgTranslationCoordinates_(), startPoint = _c.startPoint, endPoint = _c.endPoint;
              translateStart = startPoint.x + "px, " + startPoint.y + "px";
              translateEnd = endPoint.x + "px, " + endPoint.y + "px";
          }
          this.adapter.updateCssVariable(VAR_FG_TRANSLATE_START, translateStart);
          this.adapter.updateCssVariable(VAR_FG_TRANSLATE_END, translateEnd);
          // Cancel any ongoing activation/deactivation animations
          clearTimeout(this.activationTimer_);
          clearTimeout(this.fgDeactivationRemovalTimer_);
          this.rmBoundedActivationClasses_();
          this.adapter.removeClass(FG_DEACTIVATION);
          // Force layout in order to re-trigger the animation.
          this.adapter.computeBoundingRect();
          this.adapter.addClass(FG_ACTIVATION);
          this.activationTimer_ = setTimeout(function () { return _this.activationTimerCallback_(); }, DEACTIVATION_TIMEOUT_MS);
      };
      MDCRippleFoundation.prototype.getFgTranslationCoordinates_ = function () {
          var _a = this.activationState_, activationEvent = _a.activationEvent, wasActivatedByPointer = _a.wasActivatedByPointer;
          var startPoint;
          if (wasActivatedByPointer) {
              startPoint = getNormalizedEventCoords(activationEvent, this.adapter.getWindowPageOffset(), this.adapter.computeBoundingRect());
          }
          else {
              startPoint = {
                  x: this.frame_.width / 2,
                  y: this.frame_.height / 2,
              };
          }
          // Center the element around the start point.
          startPoint = {
              x: startPoint.x - (this.initialSize_ / 2),
              y: startPoint.y - (this.initialSize_ / 2),
          };
          var endPoint = {
              x: (this.frame_.width / 2) - (this.initialSize_ / 2),
              y: (this.frame_.height / 2) - (this.initialSize_ / 2),
          };
          return { startPoint: startPoint, endPoint: endPoint };
      };
      MDCRippleFoundation.prototype.runDeactivationUXLogicIfReady_ = function () {
          var _this = this;
          // This method is called both when a pointing device is released, and when the activation animation ends.
          // The deactivation animation should only run after both of those occur.
          var FG_DEACTIVATION = MDCRippleFoundation.cssClasses.FG_DEACTIVATION;
          var _a = this.activationState_, hasDeactivationUXRun = _a.hasDeactivationUXRun, isActivated = _a.isActivated;
          var activationHasEnded = hasDeactivationUXRun || !isActivated;
          if (activationHasEnded && this.activationAnimationHasEnded_) {
              this.rmBoundedActivationClasses_();
              this.adapter.addClass(FG_DEACTIVATION);
              this.fgDeactivationRemovalTimer_ = setTimeout(function () {
                  _this.adapter.removeClass(FG_DEACTIVATION);
              }, numbers.FG_DEACTIVATION_MS);
          }
      };
      MDCRippleFoundation.prototype.rmBoundedActivationClasses_ = function () {
          var FG_ACTIVATION = MDCRippleFoundation.cssClasses.FG_ACTIVATION;
          this.adapter.removeClass(FG_ACTIVATION);
          this.activationAnimationHasEnded_ = false;
          this.adapter.computeBoundingRect();
      };
      MDCRippleFoundation.prototype.resetActivationState_ = function () {
          var _this = this;
          this.previousActivationEvent_ = this.activationState_.activationEvent;
          this.activationState_ = this.defaultActivationState_();
          // Touch devices may fire additional events for the same interaction within a short time.
          // Store the previous event until it's safe to assume that subsequent events are for new interactions.
          setTimeout(function () { return _this.previousActivationEvent_ = undefined; }, MDCRippleFoundation.numbers.TAP_DELAY_MS);
      };
      MDCRippleFoundation.prototype.deactivate_ = function () {
          var _this = this;
          var activationState = this.activationState_;
          // This can happen in scenarios such as when you have a keyup event that blurs the element.
          if (!activationState.isActivated) {
              return;
          }
          var state = __assign({}, activationState);
          if (activationState.isProgrammatic) {
              requestAnimationFrame(function () { return _this.animateDeactivation_(state); });
              this.resetActivationState_();
          }
          else {
              this.deregisterDeactivationHandlers_();
              requestAnimationFrame(function () {
                  _this.activationState_.hasDeactivationUXRun = true;
                  _this.animateDeactivation_(state);
                  _this.resetActivationState_();
              });
          }
      };
      MDCRippleFoundation.prototype.animateDeactivation_ = function (_a) {
          var wasActivatedByPointer = _a.wasActivatedByPointer, wasElementMadeActive = _a.wasElementMadeActive;
          if (wasActivatedByPointer || wasElementMadeActive) {
              this.runDeactivationUXLogicIfReady_();
          }
      };
      MDCRippleFoundation.prototype.layoutInternal_ = function () {
          var _this = this;
          this.frame_ = this.adapter.computeBoundingRect();
          var maxDim = Math.max(this.frame_.height, this.frame_.width);
          // Surface diameter is treated differently for unbounded vs. bounded ripples.
          // Unbounded ripple diameter is calculated smaller since the surface is expected to already be padded appropriately
          // to extend the hitbox, and the ripple is expected to meet the edges of the padded hitbox (which is typically
          // square). Bounded ripples, on the other hand, are fully expected to expand beyond the surface's longest diameter
          // (calculated based on the diagonal plus a constant padding), and are clipped at the surface's border via
          // `overflow: hidden`.
          var getBoundedRadius = function () {
              var hypotenuse = Math.sqrt(Math.pow(_this.frame_.width, 2) + Math.pow(_this.frame_.height, 2));
              return hypotenuse + MDCRippleFoundation.numbers.PADDING;
          };
          this.maxRadius_ = this.adapter.isUnbounded() ? maxDim : getBoundedRadius();
          // Ripple is sized as a fraction of the largest dimension of the surface, then scales up using a CSS scale transform
          var initialSize = Math.floor(maxDim * MDCRippleFoundation.numbers.INITIAL_ORIGIN_SCALE);
          // Unbounded ripple size should always be even number to equally center align.
          if (this.adapter.isUnbounded() && initialSize % 2 !== 0) {
              this.initialSize_ = initialSize - 1;
          }
          else {
              this.initialSize_ = initialSize;
          }
          this.fgScale_ = "" + this.maxRadius_ / this.initialSize_;
          this.updateLayoutCssVars_();
      };
      MDCRippleFoundation.prototype.updateLayoutCssVars_ = function () {
          var _a = MDCRippleFoundation.strings, VAR_FG_SIZE = _a.VAR_FG_SIZE, VAR_LEFT = _a.VAR_LEFT, VAR_TOP = _a.VAR_TOP, VAR_FG_SCALE = _a.VAR_FG_SCALE;
          this.adapter.updateCssVariable(VAR_FG_SIZE, this.initialSize_ + "px");
          this.adapter.updateCssVariable(VAR_FG_SCALE, this.fgScale_);
          if (this.adapter.isUnbounded()) {
              this.unboundedCoords_ = {
                  left: Math.round((this.frame_.width / 2) - (this.initialSize_ / 2)),
                  top: Math.round((this.frame_.height / 2) - (this.initialSize_ / 2)),
              };
              this.adapter.updateCssVariable(VAR_LEFT, this.unboundedCoords_.left + "px");
              this.adapter.updateCssVariable(VAR_TOP, this.unboundedCoords_.top + "px");
          }
      };
      return MDCRippleFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCRipple = /** @class */ (function (_super) {
      __extends(MDCRipple, _super);
      function MDCRipple() {
          var _this = _super !== null && _super.apply(this, arguments) || this;
          _this.disabled = false;
          return _this;
      }
      MDCRipple.attachTo = function (root, opts) {
          if (opts === void 0) { opts = { isUnbounded: undefined }; }
          var ripple = new MDCRipple(root);
          // Only override unbounded behavior if option is explicitly specified
          if (opts.isUnbounded !== undefined) {
              ripple.unbounded = opts.isUnbounded;
          }
          return ripple;
      };
      MDCRipple.createAdapter = function (instance) {
          return {
              addClass: function (className) { return instance.root.classList.add(className); },
              browserSupportsCssVars: function () { return supportsCssVariables(window); },
              computeBoundingRect: function () { return instance.root.getBoundingClientRect(); },
              containsEventTarget: function (target) { return instance.root.contains(target); },
              deregisterDocumentInteractionHandler: function (evtType, handler) {
                  return document.documentElement.removeEventListener(evtType, handler, applyPassive());
              },
              deregisterInteractionHandler: function (evtType, handler) {
                  return instance.root
                      .removeEventListener(evtType, handler, applyPassive());
              },
              deregisterResizeHandler: function (handler) {
                  return window.removeEventListener('resize', handler);
              },
              getWindowPageOffset: function () {
                  return ({ x: window.pageXOffset, y: window.pageYOffset });
              },
              isSurfaceActive: function () { return matches(instance.root, ':active'); },
              isSurfaceDisabled: function () { return Boolean(instance.disabled); },
              isUnbounded: function () { return Boolean(instance.unbounded); },
              registerDocumentInteractionHandler: function (evtType, handler) {
                  return document.documentElement.addEventListener(evtType, handler, applyPassive());
              },
              registerInteractionHandler: function (evtType, handler) {
                  return instance.root
                      .addEventListener(evtType, handler, applyPassive());
              },
              registerResizeHandler: function (handler) {
                  return window.addEventListener('resize', handler);
              },
              removeClass: function (className) { return instance.root.classList.remove(className); },
              updateCssVariable: function (varName, value) {
                  return instance.root.style.setProperty(varName, value);
              },
          };
      };
      Object.defineProperty(MDCRipple.prototype, "unbounded", {
          get: function () {
              return Boolean(this.unbounded_);
          },
          set: function (unbounded) {
              this.unbounded_ = Boolean(unbounded);
              this.setUnbounded_();
          },
          enumerable: true,
          configurable: true
      });
      MDCRipple.prototype.activate = function () {
          this.foundation.activate();
      };
      MDCRipple.prototype.deactivate = function () {
          this.foundation.deactivate();
      };
      MDCRipple.prototype.layout = function () {
          this.foundation.layout();
      };
      MDCRipple.prototype.getDefaultFoundation = function () {
          return new MDCRippleFoundation(MDCRipple.createAdapter(this));
      };
      MDCRipple.prototype.initialSyncWithDOM = function () {
          var root = this.root;
          this.unbounded = 'mdcRippleIsUnbounded' in root.dataset;
      };
      /**
       * Closure Compiler throws an access control error when directly accessing a
       * protected or private property inside a getter/setter, like unbounded above.
       * By accessing the protected property inside a method, we solve that problem.
       * That's why this function exists.
       */
      MDCRipple.prototype.setUnbounded_ = function () {
          this.foundation.setUnbounded(Boolean(this.unbounded_));
      };
      return MDCRipple;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses$1 = {
      ANIM_CHECKED_INDETERMINATE: 'mdc-checkbox--anim-checked-indeterminate',
      ANIM_CHECKED_UNCHECKED: 'mdc-checkbox--anim-checked-unchecked',
      ANIM_INDETERMINATE_CHECKED: 'mdc-checkbox--anim-indeterminate-checked',
      ANIM_INDETERMINATE_UNCHECKED: 'mdc-checkbox--anim-indeterminate-unchecked',
      ANIM_UNCHECKED_CHECKED: 'mdc-checkbox--anim-unchecked-checked',
      ANIM_UNCHECKED_INDETERMINATE: 'mdc-checkbox--anim-unchecked-indeterminate',
      BACKGROUND: 'mdc-checkbox__background',
      CHECKED: 'mdc-checkbox--checked',
      CHECKMARK: 'mdc-checkbox__checkmark',
      CHECKMARK_PATH: 'mdc-checkbox__checkmark-path',
      DISABLED: 'mdc-checkbox--disabled',
      INDETERMINATE: 'mdc-checkbox--indeterminate',
      MIXEDMARK: 'mdc-checkbox__mixedmark',
      NATIVE_CONTROL: 'mdc-checkbox__native-control',
      ROOT: 'mdc-checkbox',
      SELECTED: 'mdc-checkbox--selected',
      UPGRADED: 'mdc-checkbox--upgraded',
  };
  var strings$1 = {
      ARIA_CHECKED_ATTR: 'aria-checked',
      ARIA_CHECKED_INDETERMINATE_VALUE: 'mixed',
      DATA_INDETERMINATE_ATTR: 'data-indeterminate',
      NATIVE_CONTROL_SELECTOR: '.mdc-checkbox__native-control',
      TRANSITION_STATE_CHECKED: 'checked',
      TRANSITION_STATE_INDETERMINATE: 'indeterminate',
      TRANSITION_STATE_INIT: 'init',
      TRANSITION_STATE_UNCHECKED: 'unchecked',
  };
  var numbers$1 = {
      ANIM_END_LATCH_MS: 250,
  };

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCCheckboxFoundation = /** @class */ (function (_super) {
      __extends(MDCCheckboxFoundation, _super);
      function MDCCheckboxFoundation(adapter) {
          var _this = _super.call(this, __assign(__assign({}, MDCCheckboxFoundation.defaultAdapter), adapter)) || this;
          _this.currentCheckState_ = strings$1.TRANSITION_STATE_INIT;
          _this.currentAnimationClass_ = '';
          _this.animEndLatchTimer_ = 0;
          _this.enableAnimationEndHandler_ = false;
          return _this;
      }
      Object.defineProperty(MDCCheckboxFoundation, "cssClasses", {
          get: function () {
              return cssClasses$1;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckboxFoundation, "strings", {
          get: function () {
              return strings$1;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckboxFoundation, "numbers", {
          get: function () {
              return numbers$1;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckboxFoundation, "defaultAdapter", {
          get: function () {
              return {
                  addClass: function () { return undefined; },
                  forceLayout: function () { return undefined; },
                  hasNativeControl: function () { return false; },
                  isAttachedToDOM: function () { return false; },
                  isChecked: function () { return false; },
                  isIndeterminate: function () { return false; },
                  removeClass: function () { return undefined; },
                  removeNativeControlAttr: function () { return undefined; },
                  setNativeControlAttr: function () { return undefined; },
                  setNativeControlDisabled: function () { return undefined; },
              };
          },
          enumerable: true,
          configurable: true
      });
      MDCCheckboxFoundation.prototype.init = function () {
          this.currentCheckState_ = this.determineCheckState_();
          this.updateAriaChecked_();
          this.adapter.addClass(cssClasses$1.UPGRADED);
      };
      MDCCheckboxFoundation.prototype.destroy = function () {
          clearTimeout(this.animEndLatchTimer_);
      };
      MDCCheckboxFoundation.prototype.setDisabled = function (disabled) {
          this.adapter.setNativeControlDisabled(disabled);
          if (disabled) {
              this.adapter.addClass(cssClasses$1.DISABLED);
          }
          else {
              this.adapter.removeClass(cssClasses$1.DISABLED);
          }
      };
      /**
       * Handles the animationend event for the checkbox
       */
      MDCCheckboxFoundation.prototype.handleAnimationEnd = function () {
          var _this = this;
          if (!this.enableAnimationEndHandler_) {
              return;
          }
          clearTimeout(this.animEndLatchTimer_);
          this.animEndLatchTimer_ = setTimeout(function () {
              _this.adapter.removeClass(_this.currentAnimationClass_);
              _this.enableAnimationEndHandler_ = false;
          }, numbers$1.ANIM_END_LATCH_MS);
      };
      /**
       * Handles the change event for the checkbox
       */
      MDCCheckboxFoundation.prototype.handleChange = function () {
          this.transitionCheckState_();
      };
      MDCCheckboxFoundation.prototype.transitionCheckState_ = function () {
          if (!this.adapter.hasNativeControl()) {
              return;
          }
          var oldState = this.currentCheckState_;
          var newState = this.determineCheckState_();
          if (oldState === newState) {
              return;
          }
          this.updateAriaChecked_();
          var TRANSITION_STATE_UNCHECKED = strings$1.TRANSITION_STATE_UNCHECKED;
          var SELECTED = cssClasses$1.SELECTED;
          if (newState === TRANSITION_STATE_UNCHECKED) {
              this.adapter.removeClass(SELECTED);
          }
          else {
              this.adapter.addClass(SELECTED);
          }
          // Check to ensure that there isn't a previously existing animation class, in case for example
          // the user interacted with the checkbox before the animation was finished.
          if (this.currentAnimationClass_.length > 0) {
              clearTimeout(this.animEndLatchTimer_);
              this.adapter.forceLayout();
              this.adapter.removeClass(this.currentAnimationClass_);
          }
          this.currentAnimationClass_ = this.getTransitionAnimationClass_(oldState, newState);
          this.currentCheckState_ = newState;
          // Check for parentNode so that animations are only run when the element is attached
          // to the DOM.
          if (this.adapter.isAttachedToDOM() &&
              this.currentAnimationClass_.length > 0) {
              this.adapter.addClass(this.currentAnimationClass_);
              this.enableAnimationEndHandler_ = true;
          }
      };
      MDCCheckboxFoundation.prototype.determineCheckState_ = function () {
          var TRANSITION_STATE_INDETERMINATE = strings$1.TRANSITION_STATE_INDETERMINATE, TRANSITION_STATE_CHECKED = strings$1.TRANSITION_STATE_CHECKED, TRANSITION_STATE_UNCHECKED = strings$1.TRANSITION_STATE_UNCHECKED;
          if (this.adapter.isIndeterminate()) {
              return TRANSITION_STATE_INDETERMINATE;
          }
          return this.adapter.isChecked() ? TRANSITION_STATE_CHECKED :
              TRANSITION_STATE_UNCHECKED;
      };
      MDCCheckboxFoundation.prototype.getTransitionAnimationClass_ = function (oldState, newState) {
          var TRANSITION_STATE_INIT = strings$1.TRANSITION_STATE_INIT, TRANSITION_STATE_CHECKED = strings$1.TRANSITION_STATE_CHECKED, TRANSITION_STATE_UNCHECKED = strings$1.TRANSITION_STATE_UNCHECKED;
          var _a = MDCCheckboxFoundation.cssClasses, ANIM_UNCHECKED_CHECKED = _a.ANIM_UNCHECKED_CHECKED, ANIM_UNCHECKED_INDETERMINATE = _a.ANIM_UNCHECKED_INDETERMINATE, ANIM_CHECKED_UNCHECKED = _a.ANIM_CHECKED_UNCHECKED, ANIM_CHECKED_INDETERMINATE = _a.ANIM_CHECKED_INDETERMINATE, ANIM_INDETERMINATE_CHECKED = _a.ANIM_INDETERMINATE_CHECKED, ANIM_INDETERMINATE_UNCHECKED = _a.ANIM_INDETERMINATE_UNCHECKED;
          switch (oldState) {
              case TRANSITION_STATE_INIT:
                  if (newState === TRANSITION_STATE_UNCHECKED) {
                      return '';
                  }
                  return newState === TRANSITION_STATE_CHECKED ? ANIM_INDETERMINATE_CHECKED : ANIM_INDETERMINATE_UNCHECKED;
              case TRANSITION_STATE_UNCHECKED:
                  return newState === TRANSITION_STATE_CHECKED ? ANIM_UNCHECKED_CHECKED : ANIM_UNCHECKED_INDETERMINATE;
              case TRANSITION_STATE_CHECKED:
                  return newState === TRANSITION_STATE_UNCHECKED ? ANIM_CHECKED_UNCHECKED : ANIM_CHECKED_INDETERMINATE;
              default: // TRANSITION_STATE_INDETERMINATE
                  return newState === TRANSITION_STATE_CHECKED ? ANIM_INDETERMINATE_CHECKED : ANIM_INDETERMINATE_UNCHECKED;
          }
      };
      MDCCheckboxFoundation.prototype.updateAriaChecked_ = function () {
          // Ensure aria-checked is set to mixed if checkbox is in indeterminate state.
          if (this.adapter.isIndeterminate()) {
              this.adapter.setNativeControlAttr(strings$1.ARIA_CHECKED_ATTR, strings$1.ARIA_CHECKED_INDETERMINATE_VALUE);
          }
          else {
              // The on/off state does not need to keep track of aria-checked, since
              // the screenreader uses the checked property on the checkbox element.
              this.adapter.removeNativeControlAttr(strings$1.ARIA_CHECKED_ATTR);
          }
      };
      return MDCCheckboxFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var CB_PROTO_PROPS = ['checked', 'indeterminate'];
  var MDCCheckbox = /** @class */ (function (_super) {
      __extends(MDCCheckbox, _super);
      function MDCCheckbox() {
          var _this = _super !== null && _super.apply(this, arguments) || this;
          _this.ripple_ = _this.createRipple_();
          return _this;
      }
      MDCCheckbox.attachTo = function (root) {
          return new MDCCheckbox(root);
      };
      Object.defineProperty(MDCCheckbox.prototype, "ripple", {
          get: function () {
              return this.ripple_;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckbox.prototype, "checked", {
          get: function () {
              return this.nativeControl_.checked;
          },
          set: function (checked) {
              this.nativeControl_.checked = checked;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckbox.prototype, "indeterminate", {
          get: function () {
              return this.nativeControl_.indeterminate;
          },
          set: function (indeterminate) {
              this.nativeControl_.indeterminate = indeterminate;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckbox.prototype, "disabled", {
          get: function () {
              return this.nativeControl_.disabled;
          },
          set: function (disabled) {
              this.foundation.setDisabled(disabled);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCCheckbox.prototype, "value", {
          get: function () {
              return this.nativeControl_.value;
          },
          set: function (value) {
              this.nativeControl_.value = value;
          },
          enumerable: true,
          configurable: true
      });
      MDCCheckbox.prototype.initialize = function () {
          var DATA_INDETERMINATE_ATTR = strings$1.DATA_INDETERMINATE_ATTR;
          this.nativeControl_.indeterminate =
              this.nativeControl_.getAttribute(DATA_INDETERMINATE_ATTR) === 'true';
          this.nativeControl_.removeAttribute(DATA_INDETERMINATE_ATTR);
      };
      MDCCheckbox.prototype.initialSyncWithDOM = function () {
          var _this = this;
          this.handleChange_ = function () { return _this.foundation.handleChange(); };
          this.handleAnimationEnd_ = function () { return _this.foundation.handleAnimationEnd(); };
          this.nativeControl_.addEventListener('change', this.handleChange_);
          this.listen(getCorrectEventName(window, 'animationend'), this.handleAnimationEnd_);
          this.installPropertyChangeHooks_();
      };
      MDCCheckbox.prototype.destroy = function () {
          this.ripple_.destroy();
          this.nativeControl_.removeEventListener('change', this.handleChange_);
          this.unlisten(getCorrectEventName(window, 'animationend'), this.handleAnimationEnd_);
          this.uninstallPropertyChangeHooks_();
          _super.prototype.destroy.call(this);
      };
      MDCCheckbox.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          var adapter = {
              addClass: function (className) { return _this.root.classList.add(className); },
              forceLayout: function () { return _this.root.offsetWidth; },
              hasNativeControl: function () { return !!_this.nativeControl_; },
              isAttachedToDOM: function () { return Boolean(_this.root.parentNode); },
              isChecked: function () { return _this.checked; },
              isIndeterminate: function () { return _this.indeterminate; },
              removeClass: function (className) {
                  _this.root.classList.remove(className);
              },
              removeNativeControlAttr: function (attr) {
                  _this.nativeControl_.removeAttribute(attr);
              },
              setNativeControlAttr: function (attr, value) {
                  _this.nativeControl_.setAttribute(attr, value);
              },
              setNativeControlDisabled: function (disabled) {
                  _this.nativeControl_.disabled = disabled;
              },
          };
          return new MDCCheckboxFoundation(adapter);
      };
      MDCCheckbox.prototype.createRipple_ = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          var adapter = __assign(__assign({}, MDCRipple.createAdapter(this)), { deregisterInteractionHandler: function (evtType, handler) { return _this.nativeControl_.removeEventListener(evtType, handler, applyPassive()); }, isSurfaceActive: function () { return matches(_this.nativeControl_, ':active'); }, isUnbounded: function () { return true; }, registerInteractionHandler: function (evtType, handler) { return _this.nativeControl_.addEventListener(evtType, handler, applyPassive()); } });
          return new MDCRipple(this.root, new MDCRippleFoundation(adapter));
      };
      MDCCheckbox.prototype.installPropertyChangeHooks_ = function () {
          var _this = this;
          var nativeCb = this.nativeControl_;
          var cbProto = Object.getPrototypeOf(nativeCb);
          CB_PROTO_PROPS.forEach(function (controlState) {
              var desc = Object.getOwnPropertyDescriptor(cbProto, controlState);
              // We have to check for this descriptor, since some browsers (Safari) don't support its return.
              // See: https://bugs.webkit.org/show_bug.cgi?id=49739
              if (!validDescriptor(desc)) {
                  return;
              }
              // Type cast is needed for compatibility with Closure Compiler.
              var nativeGetter = desc.get;
              var nativeCbDesc = {
                  configurable: desc.configurable,
                  enumerable: desc.enumerable,
                  get: nativeGetter,
                  set: function (state) {
                      desc.set.call(nativeCb, state);
                      _this.foundation.handleChange();
                  },
              };
              Object.defineProperty(nativeCb, controlState, nativeCbDesc);
          });
      };
      MDCCheckbox.prototype.uninstallPropertyChangeHooks_ = function () {
          var nativeCb = this.nativeControl_;
          var cbProto = Object.getPrototypeOf(nativeCb);
          CB_PROTO_PROPS.forEach(function (controlState) {
              var desc = Object.getOwnPropertyDescriptor(cbProto, controlState);
              if (!validDescriptor(desc)) {
                  return;
              }
              Object.defineProperty(nativeCb, controlState, desc);
          });
      };
      Object.defineProperty(MDCCheckbox.prototype, "nativeControl_", {
          get: function () {
              var NATIVE_CONTROL_SELECTOR = strings$1.NATIVE_CONTROL_SELECTOR;
              var el = this.root.querySelector(NATIVE_CONTROL_SELECTOR);
              if (!el) {
                  throw new Error("Checkbox component requires a " + NATIVE_CONTROL_SELECTOR + " element");
              }
              return el;
          },
          enumerable: true,
          configurable: true
      });
      return MDCCheckbox;
  }(MDCComponent));
  function validDescriptor(inputPropDesc) {
      return !!inputPropDesc && typeof inputPropDesc.set === 'function';
  }

  var isArray = Array.isArray;

  function cc(obj) {
    var out = "";

    if (typeof obj === "string" || typeof obj === "number") return obj || ""

    if (isArray(obj))
      for (var k = 0, tmp; k < obj.length; k++) {
        if ((tmp = cc(obj[k])) !== "") {
          out += (out && " ") + tmp;
        }
      }
    else
      for (var k in obj) {
        if (obj.hasOwnProperty(k) && obj[k]) out += (out && " ") + k;
      }

    return out
  }

  const _tmpl$ = template(`<div class="vf-field__row"><div class="vf-field__checkbox-container"><div class="mdc-touch-target-wrapper"><div class="vf-field__control mdc-form-field"><div><input type="checkbox" class="mdc-checkbox__native-control"><div class="mdc-checkbox__background"><svg class="mdc-checkbox__checkmark" viewBox="0 0 24 24"><path class="mdc-checkbox__checkmark-path" fill="none" d="M1.73,12.91 8.1,19.28 22.79,4.59"></path></svg><div class="mdc-checkbox__mixedmark"></div></div><div class="mdc-checkbox__ripple"></div></div><label></label></div></div></div></div>`, 23),
        _tmpl$2 = template(`<div class="mdc-text-field-helper-line"><div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent"></div></div>`, 4);
  const defaultProps = {
    'checked': undefined,
    'disabled': false,
    'error': undefined,
    'helpText': undefined,
    'id': undefined,
    'label': undefined,
    'name': undefined,
    'required': false
  };
  const VCheckboxField = customElement('vf-field-checkbox', defaultProps, (props, {
    element
  }) => {
    let control;
    let checkbox;
    noShadowDOM();
    afterEffects(() => {
      checkbox = new MDCCheckbox(control);
    });
    onCleanup(() => {
      checkbox.destroy();
    });
    return (() => {
      const _el$ = _tmpl$.cloneNode(true),
            _el$2 = _el$.firstChild,
            _el$3 = _el$2.firstChild,
            _el$4 = _el$3.firstChild,
            _el$5 = _el$4.firstChild,
            _el$6 = _el$5.firstChild,
            _el$7 = _el$5.nextSibling;

      typeof control === "function" ? control(_el$5) : control = _el$5;

      insert(_el$7, () => props.label);

      insert(_el$2, (() => {
        const _c$ = memo(() => !!(props.helpText || props.error), true);

        return () => _c$() ? (() => {
          const _el$8 = _tmpl$2.cloneNode(true),
                _el$9 = _el$8.firstChild;

          insert(_el$9, () => props.error || props.helpText);

          return _el$8;
        })() : '';
      })(), null);

      createEffect(_p$ => {
        const _v$ = cc({
          'mdc-checkbox': true,
          'mdc-checkbox--disabled': !!props.disabled
        }),
              _v$2 = props.checked,
              _v$3 = !!props.disabled,
              _v$4 = props.id + '_control',
              _v$5 = props.name,
              _v$6 = !!props.required,
              _v$7 = props.id + '_control';

        _v$ !== _p$._v$ && (_el$5.className = _p$._v$ = _v$);
        _v$2 !== _p$._v$2 && (_el$6.checked = _p$._v$2 = _v$2);
        _v$3 !== _p$._v$3 && (_el$6.disabled = _p$._v$3 = _v$3);
        _v$4 !== _p$._v$4 && (_el$6.id = _p$._v$4 = _v$4);
        _v$5 !== _p$._v$5 && (_el$6.name = _p$._v$5 = _v$5);
        _v$6 !== _p$._v$6 && (_el$6.required = _p$._v$6 = _v$6);
        _v$7 !== _p$._v$7 && (_el$7.htmlFor = _p$._v$7 = _v$7);
        return _p$;
      }, {
        _v$: undefined,
        _v$2: undefined,
        _v$3: undefined,
        _v$4: undefined,
        _v$5: undefined,
        _v$6: undefined,
        _v$7: undefined
      });

      return _el$;
    })();
  });

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses$2 = {
      LABEL_FLOAT_ABOVE: 'mdc-floating-label--float-above',
      LABEL_REQUIRED: 'mdc-floating-label--required',
      LABEL_SHAKE: 'mdc-floating-label--shake',
      ROOT: 'mdc-floating-label',
  };

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCFloatingLabelFoundation = /** @class */ (function (_super) {
      __extends(MDCFloatingLabelFoundation, _super);
      function MDCFloatingLabelFoundation(adapter) {
          var _this = _super.call(this, __assign(__assign({}, MDCFloatingLabelFoundation.defaultAdapter), adapter)) || this;
          _this.shakeAnimationEndHandler_ = function () { return _this.handleShakeAnimationEnd_(); };
          return _this;
      }
      Object.defineProperty(MDCFloatingLabelFoundation, "cssClasses", {
          get: function () {
              return cssClasses$2;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCFloatingLabelFoundation, "defaultAdapter", {
          /**
           * See {@link MDCFloatingLabelAdapter} for typing information on parameters and return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  addClass: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  getWidth: function () { return 0; },
                  registerInteractionHandler: function () { return undefined; },
                  deregisterInteractionHandler: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      MDCFloatingLabelFoundation.prototype.init = function () {
          this.adapter.registerInteractionHandler('animationend', this.shakeAnimationEndHandler_);
      };
      MDCFloatingLabelFoundation.prototype.destroy = function () {
          this.adapter.deregisterInteractionHandler('animationend', this.shakeAnimationEndHandler_);
      };
      /**
       * Returns the width of the label element.
       */
      MDCFloatingLabelFoundation.prototype.getWidth = function () {
          return this.adapter.getWidth();
      };
      /**
       * Styles the label to produce a shake animation to indicate an error.
       * @param shouldShake If true, adds the shake CSS class; otherwise, removes shake class.
       */
      MDCFloatingLabelFoundation.prototype.shake = function (shouldShake) {
          var LABEL_SHAKE = MDCFloatingLabelFoundation.cssClasses.LABEL_SHAKE;
          if (shouldShake) {
              this.adapter.addClass(LABEL_SHAKE);
          }
          else {
              this.adapter.removeClass(LABEL_SHAKE);
          }
      };
      /**
       * Styles the label to float or dock.
       * @param shouldFloat If true, adds the float CSS class; otherwise, removes float and shake classes to dock the label.
       */
      MDCFloatingLabelFoundation.prototype.float = function (shouldFloat) {
          var _a = MDCFloatingLabelFoundation.cssClasses, LABEL_FLOAT_ABOVE = _a.LABEL_FLOAT_ABOVE, LABEL_SHAKE = _a.LABEL_SHAKE;
          if (shouldFloat) {
              this.adapter.addClass(LABEL_FLOAT_ABOVE);
          }
          else {
              this.adapter.removeClass(LABEL_FLOAT_ABOVE);
              this.adapter.removeClass(LABEL_SHAKE);
          }
      };
      /**
       * Styles the label as required.
       * @param isRequired If true, adds an asterisk to the label, indicating that it is required.
       */
      MDCFloatingLabelFoundation.prototype.setRequired = function (isRequired) {
          var LABEL_REQUIRED = MDCFloatingLabelFoundation.cssClasses.LABEL_REQUIRED;
          if (isRequired) {
              this.adapter.addClass(LABEL_REQUIRED);
          }
          else {
              this.adapter.removeClass(LABEL_REQUIRED);
          }
      };
      MDCFloatingLabelFoundation.prototype.handleShakeAnimationEnd_ = function () {
          var LABEL_SHAKE = MDCFloatingLabelFoundation.cssClasses.LABEL_SHAKE;
          this.adapter.removeClass(LABEL_SHAKE);
      };
      return MDCFloatingLabelFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCFloatingLabel = /** @class */ (function (_super) {
      __extends(MDCFloatingLabel, _super);
      function MDCFloatingLabel() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCFloatingLabel.attachTo = function (root) {
          return new MDCFloatingLabel(root);
      };
      /**
       * Styles the label to produce the label shake for errors.
       * @param shouldShake If true, shakes the label by adding a CSS class; otherwise, stops shaking by removing the class.
       */
      MDCFloatingLabel.prototype.shake = function (shouldShake) {
          this.foundation.shake(shouldShake);
      };
      /**
       * Styles the label to float/dock.
       * @param shouldFloat If true, floats the label by adding a CSS class; otherwise, docks it by removing the class.
       */
      MDCFloatingLabel.prototype.float = function (shouldFloat) {
          this.foundation.float(shouldFloat);
      };
      /**
       * Styles the label as required.
       * @param isRequired If true, adds an asterisk to the label, indicating that it is required.
       */
      MDCFloatingLabel.prototype.setRequired = function (isRequired) {
          this.foundation.setRequired(isRequired);
      };
      MDCFloatingLabel.prototype.getWidth = function () {
          return this.foundation.getWidth();
      };
      MDCFloatingLabel.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = {
              addClass: function (className) { return _this.root.classList.add(className); },
              removeClass: function (className) { return _this.root.classList.remove(className); },
              getWidth: function () { return estimateScrollWidth(_this.root); },
              registerInteractionHandler: function (evtType, handler) {
                  return _this.listen(evtType, handler);
              },
              deregisterInteractionHandler: function (evtType, handler) {
                  return _this.unlisten(evtType, handler);
              },
          };
          // tslint:enable:object-literal-sort-keys
          return new MDCFloatingLabelFoundation(adapter);
      };
      return MDCFloatingLabel;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2018 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses$3 = {
      LINE_RIPPLE_ACTIVE: 'mdc-line-ripple--active',
      LINE_RIPPLE_DEACTIVATING: 'mdc-line-ripple--deactivating',
  };

  /**
   * @license
   * Copyright 2018 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCLineRippleFoundation = /** @class */ (function (_super) {
      __extends(MDCLineRippleFoundation, _super);
      function MDCLineRippleFoundation(adapter) {
          var _this = _super.call(this, __assign(__assign({}, MDCLineRippleFoundation.defaultAdapter), adapter)) || this;
          _this.transitionEndHandler_ = function (evt) { return _this.handleTransitionEnd(evt); };
          return _this;
      }
      Object.defineProperty(MDCLineRippleFoundation, "cssClasses", {
          get: function () {
              return cssClasses$3;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCLineRippleFoundation, "defaultAdapter", {
          /**
           * See {@link MDCLineRippleAdapter} for typing information on parameters and return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  addClass: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  hasClass: function () { return false; },
                  setStyle: function () { return undefined; },
                  registerEventHandler: function () { return undefined; },
                  deregisterEventHandler: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      MDCLineRippleFoundation.prototype.init = function () {
          this.adapter.registerEventHandler('transitionend', this.transitionEndHandler_);
      };
      MDCLineRippleFoundation.prototype.destroy = function () {
          this.adapter.deregisterEventHandler('transitionend', this.transitionEndHandler_);
      };
      MDCLineRippleFoundation.prototype.activate = function () {
          this.adapter.removeClass(cssClasses$3.LINE_RIPPLE_DEACTIVATING);
          this.adapter.addClass(cssClasses$3.LINE_RIPPLE_ACTIVE);
      };
      MDCLineRippleFoundation.prototype.setRippleCenter = function (xCoordinate) {
          this.adapter.setStyle('transform-origin', xCoordinate + "px center");
      };
      MDCLineRippleFoundation.prototype.deactivate = function () {
          this.adapter.addClass(cssClasses$3.LINE_RIPPLE_DEACTIVATING);
      };
      MDCLineRippleFoundation.prototype.handleTransitionEnd = function (evt) {
          // Wait for the line ripple to be either transparent or opaque
          // before emitting the animation end event
          var isDeactivating = this.adapter.hasClass(cssClasses$3.LINE_RIPPLE_DEACTIVATING);
          if (evt.propertyName === 'opacity') {
              if (isDeactivating) {
                  this.adapter.removeClass(cssClasses$3.LINE_RIPPLE_ACTIVE);
                  this.adapter.removeClass(cssClasses$3.LINE_RIPPLE_DEACTIVATING);
              }
          }
      };
      return MDCLineRippleFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2018 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCLineRipple = /** @class */ (function (_super) {
      __extends(MDCLineRipple, _super);
      function MDCLineRipple() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCLineRipple.attachTo = function (root) {
          return new MDCLineRipple(root);
      };
      /**
       * Activates the line ripple
       */
      MDCLineRipple.prototype.activate = function () {
          this.foundation.activate();
      };
      /**
       * Deactivates the line ripple
       */
      MDCLineRipple.prototype.deactivate = function () {
          this.foundation.deactivate();
      };
      /**
       * Sets the transform origin given a user's click location.
       * The `rippleCenter` is the x-coordinate of the middle of the ripple.
       */
      MDCLineRipple.prototype.setRippleCenter = function (xCoordinate) {
          this.foundation.setRippleCenter(xCoordinate);
      };
      MDCLineRipple.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = {
              addClass: function (className) { return _this.root.classList.add(className); },
              removeClass: function (className) { return _this.root.classList.remove(className); },
              hasClass: function (className) { return _this.root.classList.contains(className); },
              setStyle: function (propertyName, value) { return _this.root.style.setProperty(propertyName, value); },
              registerEventHandler: function (evtType, handler) { return _this.listen(evtType, handler); },
              deregisterEventHandler: function (evtType, handler) { return _this.unlisten(evtType, handler); },
          };
          // tslint:enable:object-literal-sort-keys
          return new MDCLineRippleFoundation(adapter);
      };
      return MDCLineRipple;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2018 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var strings$2 = {
      NOTCH_ELEMENT_SELECTOR: '.mdc-notched-outline__notch',
  };
  var numbers$2 = {
      // This should stay in sync with $mdc-notched-outline-padding * 2.
      NOTCH_ELEMENT_PADDING: 8,
  };
  var cssClasses$4 = {
      NO_LABEL: 'mdc-notched-outline--no-label',
      OUTLINE_NOTCHED: 'mdc-notched-outline--notched',
      OUTLINE_UPGRADED: 'mdc-notched-outline--upgraded',
  };

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCNotchedOutlineFoundation = /** @class */ (function (_super) {
      __extends(MDCNotchedOutlineFoundation, _super);
      function MDCNotchedOutlineFoundation(adapter) {
          return _super.call(this, __assign(__assign({}, MDCNotchedOutlineFoundation.defaultAdapter), adapter)) || this;
      }
      Object.defineProperty(MDCNotchedOutlineFoundation, "strings", {
          get: function () {
              return strings$2;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCNotchedOutlineFoundation, "cssClasses", {
          get: function () {
              return cssClasses$4;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCNotchedOutlineFoundation, "numbers", {
          get: function () {
              return numbers$2;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCNotchedOutlineFoundation, "defaultAdapter", {
          /**
           * See {@link MDCNotchedOutlineAdapter} for typing information on parameters and return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  addClass: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  setNotchWidthProperty: function () { return undefined; },
                  removeNotchWidthProperty: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      /**
       * Adds the outline notched selector and updates the notch width calculated based off of notchWidth.
       */
      MDCNotchedOutlineFoundation.prototype.notch = function (notchWidth) {
          var OUTLINE_NOTCHED = MDCNotchedOutlineFoundation.cssClasses.OUTLINE_NOTCHED;
          if (notchWidth > 0) {
              notchWidth += numbers$2.NOTCH_ELEMENT_PADDING; // Add padding from left/right.
          }
          this.adapter.setNotchWidthProperty(notchWidth);
          this.adapter.addClass(OUTLINE_NOTCHED);
      };
      /**
       * Removes notched outline selector to close the notch in the outline.
       */
      MDCNotchedOutlineFoundation.prototype.closeNotch = function () {
          var OUTLINE_NOTCHED = MDCNotchedOutlineFoundation.cssClasses.OUTLINE_NOTCHED;
          this.adapter.removeClass(OUTLINE_NOTCHED);
          this.adapter.removeNotchWidthProperty();
      };
      return MDCNotchedOutlineFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCNotchedOutline = /** @class */ (function (_super) {
      __extends(MDCNotchedOutline, _super);
      function MDCNotchedOutline() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCNotchedOutline.attachTo = function (root) {
          return new MDCNotchedOutline(root);
      };
      MDCNotchedOutline.prototype.initialSyncWithDOM = function () {
          this.notchElement_ =
              this.root.querySelector(strings$2.NOTCH_ELEMENT_SELECTOR);
          var label = this.root.querySelector('.' + MDCFloatingLabelFoundation.cssClasses.ROOT);
          if (label) {
              label.style.transitionDuration = '0s';
              this.root.classList.add(cssClasses$4.OUTLINE_UPGRADED);
              requestAnimationFrame(function () {
                  label.style.transitionDuration = '';
              });
          }
          else {
              this.root.classList.add(cssClasses$4.NO_LABEL);
          }
      };
      /**
       * Updates classes and styles to open the notch to the specified width.
       * @param notchWidth The notch width in the outline.
       */
      MDCNotchedOutline.prototype.notch = function (notchWidth) {
          this.foundation.notch(notchWidth);
      };
      /**
       * Updates classes and styles to close the notch.
       */
      MDCNotchedOutline.prototype.closeNotch = function () {
          this.foundation.closeNotch();
      };
      MDCNotchedOutline.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = {
              addClass: function (className) { return _this.root.classList.add(className); },
              removeClass: function (className) { return _this.root.classList.remove(className); },
              setNotchWidthProperty: function (width) {
                  return _this.notchElement_.style.setProperty('width', width + 'px');
              },
              removeNotchWidthProperty: function () {
                  return _this.notchElement_.style.removeProperty('width');
              },
          };
          // tslint:enable:object-literal-sort-keys
          return new MDCNotchedOutlineFoundation(adapter);
      };
      return MDCNotchedOutline;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2019 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses$5 = {
      ROOT: 'mdc-text-field-character-counter',
  };
  var strings$3 = {
      ROOT_SELECTOR: "." + cssClasses$5.ROOT,
  };

  /**
   * @license
   * Copyright 2019 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextFieldCharacterCounterFoundation = /** @class */ (function (_super) {
      __extends(MDCTextFieldCharacterCounterFoundation, _super);
      function MDCTextFieldCharacterCounterFoundation(adapter) {
          return _super.call(this, __assign(__assign({}, MDCTextFieldCharacterCounterFoundation.defaultAdapter), adapter)) || this;
      }
      Object.defineProperty(MDCTextFieldCharacterCounterFoundation, "cssClasses", {
          get: function () {
              return cssClasses$5;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldCharacterCounterFoundation, "strings", {
          get: function () {
              return strings$3;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldCharacterCounterFoundation, "defaultAdapter", {
          /**
           * See {@link MDCTextFieldCharacterCounterAdapter} for typing information on parameters and return types.
           */
          get: function () {
              return {
                  setContent: function () { return undefined; },
              };
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldCharacterCounterFoundation.prototype.setCounterValue = function (currentLength, maxLength) {
          currentLength = Math.min(currentLength, maxLength);
          this.adapter.setContent(currentLength + " / " + maxLength);
      };
      return MDCTextFieldCharacterCounterFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2019 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextFieldCharacterCounter = /** @class */ (function (_super) {
      __extends(MDCTextFieldCharacterCounter, _super);
      function MDCTextFieldCharacterCounter() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCTextFieldCharacterCounter.attachTo = function (root) {
          return new MDCTextFieldCharacterCounter(root);
      };
      Object.defineProperty(MDCTextFieldCharacterCounter.prototype, "foundationForTextField", {
          // Provided for access by MDCTextField component
          get: function () {
              return this.foundation;
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldCharacterCounter.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          var adapter = {
              setContent: function (content) {
                  _this.root.textContent = content;
              },
          };
          return new MDCTextFieldCharacterCounterFoundation(adapter);
      };
      return MDCTextFieldCharacterCounter;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var strings$4 = {
      ARIA_CONTROLS: 'aria-controls',
      ARIA_DESCRIBEDBY: 'aria-describedby',
      INPUT_SELECTOR: '.mdc-text-field__input',
      LABEL_SELECTOR: '.mdc-floating-label',
      LEADING_ICON_SELECTOR: '.mdc-text-field__icon--leading',
      LINE_RIPPLE_SELECTOR: '.mdc-line-ripple',
      OUTLINE_SELECTOR: '.mdc-notched-outline',
      PREFIX_SELECTOR: '.mdc-text-field__affix--prefix',
      SUFFIX_SELECTOR: '.mdc-text-field__affix--suffix',
      TRAILING_ICON_SELECTOR: '.mdc-text-field__icon--trailing'
  };
  var cssClasses$6 = {
      DISABLED: 'mdc-text-field--disabled',
      FOCUSED: 'mdc-text-field--focused',
      HELPER_LINE: 'mdc-text-field-helper-line',
      INVALID: 'mdc-text-field--invalid',
      LABEL_FLOATING: 'mdc-text-field--label-floating',
      NO_LABEL: 'mdc-text-field--no-label',
      OUTLINED: 'mdc-text-field--outlined',
      ROOT: 'mdc-text-field',
      TEXTAREA: 'mdc-text-field--textarea',
      WITH_LEADING_ICON: 'mdc-text-field--with-leading-icon',
      WITH_TRAILING_ICON: 'mdc-text-field--with-trailing-icon',
  };
  var numbers$3 = {
      LABEL_SCALE: 0.75,
  };
  /**
   * Whitelist based off of https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/HTML5/Constraint_validation
   * under the "Validation-related attributes" section.
   */
  var VALIDATION_ATTR_WHITELIST = [
      'pattern', 'min', 'max', 'required', 'step', 'minlength', 'maxlength',
  ];
  /**
   * Label should always float for these types as they show some UI even if value is empty.
   */
  var ALWAYS_FLOAT_TYPES = [
      'color', 'date', 'datetime-local', 'month', 'range', 'time', 'week',
  ];

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var POINTERDOWN_EVENTS = ['mousedown', 'touchstart'];
  var INTERACTION_EVENTS = ['click', 'keydown'];
  var MDCTextFieldFoundation = /** @class */ (function (_super) {
      __extends(MDCTextFieldFoundation, _super);
      /**
       * @param adapter
       * @param foundationMap Map from subcomponent names to their subfoundations.
       */
      function MDCTextFieldFoundation(adapter, foundationMap) {
          if (foundationMap === void 0) { foundationMap = {}; }
          var _this = _super.call(this, __assign(__assign({}, MDCTextFieldFoundation.defaultAdapter), adapter)) || this;
          _this.isFocused_ = false;
          _this.receivedUserInput_ = false;
          _this.isValid_ = true;
          _this.useNativeValidation_ = true;
          _this.validateOnValueChange_ = true;
          _this.helperText_ = foundationMap.helperText;
          _this.characterCounter_ = foundationMap.characterCounter;
          _this.leadingIcon_ = foundationMap.leadingIcon;
          _this.trailingIcon_ = foundationMap.trailingIcon;
          _this.inputFocusHandler_ = function () { return _this.activateFocus(); };
          _this.inputBlurHandler_ = function () { return _this.deactivateFocus(); };
          _this.inputInputHandler_ = function () { return _this.handleInput(); };
          _this.setPointerXOffset_ = function (evt) { return _this.setTransformOrigin(evt); };
          _this.textFieldInteractionHandler_ = function () { return _this.handleTextFieldInteraction(); };
          _this.validationAttributeChangeHandler_ = function (attributesList) {
              return _this.handleValidationAttributeChange(attributesList);
          };
          return _this;
      }
      Object.defineProperty(MDCTextFieldFoundation, "cssClasses", {
          get: function () {
              return cssClasses$6;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation, "strings", {
          get: function () {
              return strings$4;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation, "numbers", {
          get: function () {
              return numbers$3;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation.prototype, "shouldAlwaysFloat_", {
          get: function () {
              var type = this.getNativeInput_().type;
              return ALWAYS_FLOAT_TYPES.indexOf(type) >= 0;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation.prototype, "shouldFloat", {
          get: function () {
              return this.shouldAlwaysFloat_ || this.isFocused_ || !!this.getValue() ||
                  this.isBadInput_();
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation.prototype, "shouldShake", {
          get: function () {
              return !this.isFocused_ && !this.isValid() && !!this.getValue();
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldFoundation, "defaultAdapter", {
          /**
           * See {@link MDCTextFieldAdapter} for typing information on parameters and
           * return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  addClass: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  hasClass: function () { return true; },
                  setInputAttr: function () { return undefined; },
                  removeInputAttr: function () { return undefined; },
                  registerTextFieldInteractionHandler: function () { return undefined; },
                  deregisterTextFieldInteractionHandler: function () { return undefined; },
                  registerInputInteractionHandler: function () { return undefined; },
                  deregisterInputInteractionHandler: function () { return undefined; },
                  registerValidationAttributeChangeHandler: function () {
                      return new MutationObserver(function () { return undefined; });
                  },
                  deregisterValidationAttributeChangeHandler: function () { return undefined; },
                  getNativeInput: function () { return null; },
                  isFocused: function () { return false; },
                  activateLineRipple: function () { return undefined; },
                  deactivateLineRipple: function () { return undefined; },
                  setLineRippleTransformOrigin: function () { return undefined; },
                  shakeLabel: function () { return undefined; },
                  floatLabel: function () { return undefined; },
                  setLabelRequired: function () { return undefined; },
                  hasLabel: function () { return false; },
                  getLabelWidth: function () { return 0; },
                  hasOutline: function () { return false; },
                  notchOutline: function () { return undefined; },
                  closeOutline: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldFoundation.prototype.init = function () {
          var _this = this;
          if (this.adapter.hasLabel() && this.getNativeInput_().required) {
              this.adapter.setLabelRequired(true);
          }
          if (this.adapter.isFocused()) {
              this.inputFocusHandler_();
          }
          else if (this.adapter.hasLabel() && this.shouldFloat) {
              this.notchOutline(true);
              this.adapter.floatLabel(true);
              this.styleFloating_(true);
          }
          this.adapter.registerInputInteractionHandler('focus', this.inputFocusHandler_);
          this.adapter.registerInputInteractionHandler('blur', this.inputBlurHandler_);
          this.adapter.registerInputInteractionHandler('input', this.inputInputHandler_);
          POINTERDOWN_EVENTS.forEach(function (evtType) {
              _this.adapter.registerInputInteractionHandler(evtType, _this.setPointerXOffset_);
          });
          INTERACTION_EVENTS.forEach(function (evtType) {
              _this.adapter.registerTextFieldInteractionHandler(evtType, _this.textFieldInteractionHandler_);
          });
          this.validationObserver_ =
              this.adapter.registerValidationAttributeChangeHandler(this.validationAttributeChangeHandler_);
          this.setCharacterCounter_(this.getValue().length);
      };
      MDCTextFieldFoundation.prototype.destroy = function () {
          var _this = this;
          this.adapter.deregisterInputInteractionHandler('focus', this.inputFocusHandler_);
          this.adapter.deregisterInputInteractionHandler('blur', this.inputBlurHandler_);
          this.adapter.deregisterInputInteractionHandler('input', this.inputInputHandler_);
          POINTERDOWN_EVENTS.forEach(function (evtType) {
              _this.adapter.deregisterInputInteractionHandler(evtType, _this.setPointerXOffset_);
          });
          INTERACTION_EVENTS.forEach(function (evtType) {
              _this.adapter.deregisterTextFieldInteractionHandler(evtType, _this.textFieldInteractionHandler_);
          });
          this.adapter.deregisterValidationAttributeChangeHandler(this.validationObserver_);
      };
      /**
       * Handles user interactions with the Text Field.
       */
      MDCTextFieldFoundation.prototype.handleTextFieldInteraction = function () {
          var nativeInput = this.adapter.getNativeInput();
          if (nativeInput && nativeInput.disabled) {
              return;
          }
          this.receivedUserInput_ = true;
      };
      /**
       * Handles validation attribute changes
       */
      MDCTextFieldFoundation.prototype.handleValidationAttributeChange = function (attributesList) {
          var _this = this;
          attributesList.some(function (attributeName) {
              if (VALIDATION_ATTR_WHITELIST.indexOf(attributeName) > -1) {
                  _this.styleValidity_(true);
                  _this.adapter.setLabelRequired(_this.getNativeInput_().required);
                  return true;
              }
              return false;
          });
          if (attributesList.indexOf('maxlength') > -1) {
              this.setCharacterCounter_(this.getValue().length);
          }
      };
      /**
       * Opens/closes the notched outline.
       */
      MDCTextFieldFoundation.prototype.notchOutline = function (openNotch) {
          if (!this.adapter.hasOutline() || !this.adapter.hasLabel()) {
              return;
          }
          if (openNotch) {
              var labelWidth = this.adapter.getLabelWidth() * numbers$3.LABEL_SCALE;
              this.adapter.notchOutline(labelWidth);
          }
          else {
              this.adapter.closeOutline();
          }
      };
      /**
       * Activates the text field focus state.
       */
      MDCTextFieldFoundation.prototype.activateFocus = function () {
          this.isFocused_ = true;
          this.styleFocused_(this.isFocused_);
          this.adapter.activateLineRipple();
          if (this.adapter.hasLabel()) {
              this.notchOutline(this.shouldFloat);
              this.adapter.floatLabel(this.shouldFloat);
              this.styleFloating_(this.shouldFloat);
              this.adapter.shakeLabel(this.shouldShake);
          }
          if (this.helperText_ &&
              (this.helperText_.isPersistent() || !this.helperText_.isValidation() ||
                  !this.isValid_)) {
              this.helperText_.showToScreenReader();
          }
      };
      /**
       * Sets the line ripple's transform origin, so that the line ripple activate
       * animation will animate out from the user's click location.
       */
      MDCTextFieldFoundation.prototype.setTransformOrigin = function (evt) {
          if (this.isDisabled() || this.adapter.hasOutline()) {
              return;
          }
          var touches = evt.touches;
          var targetEvent = touches ? touches[0] : evt;
          var targetClientRect = targetEvent.target.getBoundingClientRect();
          var normalizedX = targetEvent.clientX - targetClientRect.left;
          this.adapter.setLineRippleTransformOrigin(normalizedX);
      };
      /**
       * Handles input change of text input and text area.
       */
      MDCTextFieldFoundation.prototype.handleInput = function () {
          this.autoCompleteFocus();
          this.setCharacterCounter_(this.getValue().length);
      };
      /**
       * Activates the Text Field's focus state in cases when the input value
       * changes without user input (e.g. programmatically).
       */
      MDCTextFieldFoundation.prototype.autoCompleteFocus = function () {
          if (!this.receivedUserInput_) {
              this.activateFocus();
          }
      };
      /**
       * Deactivates the Text Field's focus state.
       */
      MDCTextFieldFoundation.prototype.deactivateFocus = function () {
          this.isFocused_ = false;
          this.adapter.deactivateLineRipple();
          var isValid = this.isValid();
          this.styleValidity_(isValid);
          this.styleFocused_(this.isFocused_);
          if (this.adapter.hasLabel()) {
              this.notchOutline(this.shouldFloat);
              this.adapter.floatLabel(this.shouldFloat);
              this.styleFloating_(this.shouldFloat);
              this.adapter.shakeLabel(this.shouldShake);
          }
          if (!this.shouldFloat) {
              this.receivedUserInput_ = false;
          }
      };
      MDCTextFieldFoundation.prototype.getValue = function () {
          return this.getNativeInput_().value;
      };
      /**
       * @param value The value to set on the input Element.
       */
      MDCTextFieldFoundation.prototype.setValue = function (value) {
          // Prevent Safari from moving the caret to the end of the input when the
          // value has not changed.
          if (this.getValue() !== value) {
              this.getNativeInput_().value = value;
          }
          this.setCharacterCounter_(value.length);
          if (this.validateOnValueChange_) {
              var isValid = this.isValid();
              this.styleValidity_(isValid);
          }
          if (this.adapter.hasLabel()) {
              this.notchOutline(this.shouldFloat);
              this.adapter.floatLabel(this.shouldFloat);
              this.styleFloating_(this.shouldFloat);
              if (this.validateOnValueChange_) {
                  this.adapter.shakeLabel(this.shouldShake);
              }
          }
      };
      /**
       * @return The custom validity state, if set; otherwise, the result of a
       *     native validity check.
       */
      MDCTextFieldFoundation.prototype.isValid = function () {
          return this.useNativeValidation_ ? this.isNativeInputValid_() :
              this.isValid_;
      };
      /**
       * @param isValid Sets the custom validity state of the Text Field.
       */
      MDCTextFieldFoundation.prototype.setValid = function (isValid) {
          this.isValid_ = isValid;
          this.styleValidity_(isValid);
          var shouldShake = !isValid && !this.isFocused_ && !!this.getValue();
          if (this.adapter.hasLabel()) {
              this.adapter.shakeLabel(shouldShake);
          }
      };
      /**
       * @param shouldValidate Whether or not validity should be updated on
       *     value change.
       */
      MDCTextFieldFoundation.prototype.setValidateOnValueChange = function (shouldValidate) {
          this.validateOnValueChange_ = shouldValidate;
      };
      /**
       * @return Whether or not validity should be updated on value change. `true`
       *     by default.
       */
      MDCTextFieldFoundation.prototype.getValidateOnValueChange = function () {
          return this.validateOnValueChange_;
      };
      /**
       * Enables or disables the use of native validation. Use this for custom
       * validation.
       * @param useNativeValidation Set this to false to ignore native input
       *     validation.
       */
      MDCTextFieldFoundation.prototype.setUseNativeValidation = function (useNativeValidation) {
          this.useNativeValidation_ = useNativeValidation;
      };
      MDCTextFieldFoundation.prototype.isDisabled = function () {
          return this.getNativeInput_().disabled;
      };
      /**
       * @param disabled Sets the text-field disabled or enabled.
       */
      MDCTextFieldFoundation.prototype.setDisabled = function (disabled) {
          this.getNativeInput_().disabled = disabled;
          this.styleDisabled_(disabled);
      };
      /**
       * @param content Sets the content of the helper text.
       */
      MDCTextFieldFoundation.prototype.setHelperTextContent = function (content) {
          if (this.helperText_) {
              this.helperText_.setContent(content);
          }
      };
      /**
       * Sets the aria label of the leading icon.
       */
      MDCTextFieldFoundation.prototype.setLeadingIconAriaLabel = function (label) {
          if (this.leadingIcon_) {
              this.leadingIcon_.setAriaLabel(label);
          }
      };
      /**
       * Sets the text content of the leading icon.
       */
      MDCTextFieldFoundation.prototype.setLeadingIconContent = function (content) {
          if (this.leadingIcon_) {
              this.leadingIcon_.setContent(content);
          }
      };
      /**
       * Sets the aria label of the trailing icon.
       */
      MDCTextFieldFoundation.prototype.setTrailingIconAriaLabel = function (label) {
          if (this.trailingIcon_) {
              this.trailingIcon_.setAriaLabel(label);
          }
      };
      /**
       * Sets the text content of the trailing icon.
       */
      MDCTextFieldFoundation.prototype.setTrailingIconContent = function (content) {
          if (this.trailingIcon_) {
              this.trailingIcon_.setContent(content);
          }
      };
      /**
       * Sets character counter values that shows characters used and the total
       * character limit.
       */
      MDCTextFieldFoundation.prototype.setCharacterCounter_ = function (currentLength) {
          if (!this.characterCounter_) {
              return;
          }
          var maxLength = this.getNativeInput_().maxLength;
          if (maxLength === -1) {
              throw new Error('MDCTextFieldFoundation: Expected maxlength html property on text input or textarea.');
          }
          this.characterCounter_.setCounterValue(currentLength, maxLength);
      };
      /**
       * @return True if the Text Field input fails in converting the user-supplied
       *     value.
       */
      MDCTextFieldFoundation.prototype.isBadInput_ = function () {
          // The badInput property is not supported in IE 11 💩.
          return this.getNativeInput_().validity.badInput || false;
      };
      /**
       * @return The result of native validity checking (ValidityState.valid).
       */
      MDCTextFieldFoundation.prototype.isNativeInputValid_ = function () {
          return this.getNativeInput_().validity.valid;
      };
      /**
       * Styles the component based on the validity state.
       */
      MDCTextFieldFoundation.prototype.styleValidity_ = function (isValid) {
          var INVALID = MDCTextFieldFoundation.cssClasses.INVALID;
          if (isValid) {
              this.adapter.removeClass(INVALID);
          }
          else {
              this.adapter.addClass(INVALID);
          }
          if (this.helperText_) {
              this.helperText_.setValidity(isValid);
              // We dynamically set or unset aria-describedby for validation helper text
              // only, based on whether the field is valid
              var helperTextValidation = this.helperText_.isValidation();
              if (!helperTextValidation) {
                  return;
              }
              var helperTextVisible = this.helperText_.isVisible();
              var helperTextId = this.helperText_.getId();
              if (helperTextVisible && helperTextId) {
                  this.adapter.setInputAttr(strings$4.ARIA_DESCRIBEDBY, helperTextId);
              }
              else {
                  this.adapter.removeInputAttr(strings$4.ARIA_DESCRIBEDBY);
              }
          }
      };
      /**
       * Styles the component based on the focused state.
       */
      MDCTextFieldFoundation.prototype.styleFocused_ = function (isFocused) {
          var FOCUSED = MDCTextFieldFoundation.cssClasses.FOCUSED;
          if (isFocused) {
              this.adapter.addClass(FOCUSED);
          }
          else {
              this.adapter.removeClass(FOCUSED);
          }
      };
      /**
       * Styles the component based on the disabled state.
       */
      MDCTextFieldFoundation.prototype.styleDisabled_ = function (isDisabled) {
          var _a = MDCTextFieldFoundation.cssClasses, DISABLED = _a.DISABLED, INVALID = _a.INVALID;
          if (isDisabled) {
              this.adapter.addClass(DISABLED);
              this.adapter.removeClass(INVALID);
          }
          else {
              this.adapter.removeClass(DISABLED);
          }
          if (this.leadingIcon_) {
              this.leadingIcon_.setDisabled(isDisabled);
          }
          if (this.trailingIcon_) {
              this.trailingIcon_.setDisabled(isDisabled);
          }
      };
      /**
       * Styles the component based on the label floating state.
       */
      MDCTextFieldFoundation.prototype.styleFloating_ = function (isFloating) {
          var LABEL_FLOATING = MDCTextFieldFoundation.cssClasses.LABEL_FLOATING;
          if (isFloating) {
              this.adapter.addClass(LABEL_FLOATING);
          }
          else {
              this.adapter.removeClass(LABEL_FLOATING);
          }
      };
      /**
       * @return The native text input element from the host environment, or an
       *     object with the same shape for unit tests.
       */
      MDCTextFieldFoundation.prototype.getNativeInput_ = function () {
          // this.adapter may be undefined in foundation unit tests. This happens when
          // testdouble is creating a mock object and invokes the
          // shouldShake/shouldFloat getters (which in turn call getValue(), which
          // calls this method) before init() has been called from the MDCTextField
          // constructor. To work around that issue, we return a dummy object.
          var nativeInput = this.adapter ? this.adapter.getNativeInput() : null;
          return nativeInput || {
              disabled: false,
              maxLength: -1,
              required: false,
              type: 'input',
              validity: {
                  badInput: false,
                  valid: true,
              },
              value: '',
          };
      };
      return MDCTextFieldFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var cssClasses$7 = {
      HELPER_TEXT_PERSISTENT: 'mdc-text-field-helper-text--persistent',
      HELPER_TEXT_VALIDATION_MSG: 'mdc-text-field-helper-text--validation-msg',
      ROOT: 'mdc-text-field-helper-text',
  };
  var strings$5 = {
      ARIA_HIDDEN: 'aria-hidden',
      ROLE: 'role',
      ROOT_SELECTOR: "." + cssClasses$7.ROOT,
  };

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextFieldHelperTextFoundation = /** @class */ (function (_super) {
      __extends(MDCTextFieldHelperTextFoundation, _super);
      function MDCTextFieldHelperTextFoundation(adapter) {
          return _super.call(this, __assign(__assign({}, MDCTextFieldHelperTextFoundation.defaultAdapter), adapter)) || this;
      }
      Object.defineProperty(MDCTextFieldHelperTextFoundation, "cssClasses", {
          get: function () {
              return cssClasses$7;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldHelperTextFoundation, "strings", {
          get: function () {
              return strings$5;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldHelperTextFoundation, "defaultAdapter", {
          /**
           * See {@link MDCTextFieldHelperTextAdapter} for typing information on parameters and return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  addClass: function () { return undefined; },
                  removeClass: function () { return undefined; },
                  hasClass: function () { return false; },
                  getAttr: function () { return null; },
                  setAttr: function () { return undefined; },
                  removeAttr: function () { return undefined; },
                  setContent: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldHelperTextFoundation.prototype.getId = function () {
          return this.adapter.getAttr('id');
      };
      MDCTextFieldHelperTextFoundation.prototype.isVisible = function () {
          return this.adapter.getAttr(strings$5.ARIA_HIDDEN) !== 'true';
      };
      /**
       * Sets the content of the helper text field.
       */
      MDCTextFieldHelperTextFoundation.prototype.setContent = function (content) {
          this.adapter.setContent(content);
      };
      MDCTextFieldHelperTextFoundation.prototype.isPersistent = function () {
          return this.adapter.hasClass(cssClasses$7.HELPER_TEXT_PERSISTENT);
      };
      /**
       * @param isPersistent Sets the persistency of the helper text.
       */
      MDCTextFieldHelperTextFoundation.prototype.setPersistent = function (isPersistent) {
          if (isPersistent) {
              this.adapter.addClass(cssClasses$7.HELPER_TEXT_PERSISTENT);
          }
          else {
              this.adapter.removeClass(cssClasses$7.HELPER_TEXT_PERSISTENT);
          }
      };
      /**
       * @return whether the helper text acts as an error validation message.
       */
      MDCTextFieldHelperTextFoundation.prototype.isValidation = function () {
          return this.adapter.hasClass(cssClasses$7.HELPER_TEXT_VALIDATION_MSG);
      };
      /**
       * @param isValidation True to make the helper text act as an error validation message.
       */
      MDCTextFieldHelperTextFoundation.prototype.setValidation = function (isValidation) {
          if (isValidation) {
              this.adapter.addClass(cssClasses$7.HELPER_TEXT_VALIDATION_MSG);
          }
          else {
              this.adapter.removeClass(cssClasses$7.HELPER_TEXT_VALIDATION_MSG);
          }
      };
      /**
       * Makes the helper text visible to the screen reader.
       */
      MDCTextFieldHelperTextFoundation.prototype.showToScreenReader = function () {
          this.adapter.removeAttr(strings$5.ARIA_HIDDEN);
      };
      /**
       * Sets the validity of the helper text based on the input validity.
       */
      MDCTextFieldHelperTextFoundation.prototype.setValidity = function (inputIsValid) {
          var helperTextIsPersistent = this.adapter.hasClass(cssClasses$7.HELPER_TEXT_PERSISTENT);
          var helperTextIsValidationMsg = this.adapter.hasClass(cssClasses$7.HELPER_TEXT_VALIDATION_MSG);
          var validationMsgNeedsDisplay = helperTextIsValidationMsg && !inputIsValid;
          if (validationMsgNeedsDisplay) {
              this.showToScreenReader();
              this.adapter.setAttr(strings$5.ROLE, 'alert');
          }
          else {
              this.adapter.removeAttr(strings$5.ROLE);
          }
          if (!helperTextIsPersistent && !validationMsgNeedsDisplay) {
              this.hide_();
          }
      };
      /**
       * Hides the help text from screen readers.
       */
      MDCTextFieldHelperTextFoundation.prototype.hide_ = function () {
          this.adapter.setAttr(strings$5.ARIA_HIDDEN, 'true');
      };
      return MDCTextFieldHelperTextFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextFieldHelperText = /** @class */ (function (_super) {
      __extends(MDCTextFieldHelperText, _super);
      function MDCTextFieldHelperText() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCTextFieldHelperText.attachTo = function (root) {
          return new MDCTextFieldHelperText(root);
      };
      Object.defineProperty(MDCTextFieldHelperText.prototype, "foundationForTextField", {
          // Provided for access by MDCTextField component
          get: function () {
              return this.foundation;
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldHelperText.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = {
              addClass: function (className) { return _this.root.classList.add(className); },
              removeClass: function (className) { return _this.root.classList.remove(className); },
              hasClass: function (className) { return _this.root.classList.contains(className); },
              getAttr: function (attr) { return _this.root.getAttribute(attr); },
              setAttr: function (attr, value) { return _this.root.setAttribute(attr, value); },
              removeAttr: function (attr) { return _this.root.removeAttribute(attr); },
              setContent: function (content) {
                  _this.root.textContent = content;
              },
          };
          // tslint:enable:object-literal-sort-keys
          return new MDCTextFieldHelperTextFoundation(adapter);
      };
      return MDCTextFieldHelperText;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var strings$6 = {
      ICON_EVENT: 'MDCTextField:icon',
      ICON_ROLE: 'button',
  };
  var cssClasses$8 = {
      ROOT: 'mdc-text-field__icon',
  };

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var INTERACTION_EVENTS$1 = ['click', 'keydown'];
  var MDCTextFieldIconFoundation = /** @class */ (function (_super) {
      __extends(MDCTextFieldIconFoundation, _super);
      function MDCTextFieldIconFoundation(adapter) {
          var _this = _super.call(this, __assign(__assign({}, MDCTextFieldIconFoundation.defaultAdapter), adapter)) || this;
          _this.savedTabIndex_ = null;
          _this.interactionHandler_ = function (evt) { return _this.handleInteraction(evt); };
          return _this;
      }
      Object.defineProperty(MDCTextFieldIconFoundation, "strings", {
          get: function () {
              return strings$6;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldIconFoundation, "cssClasses", {
          get: function () {
              return cssClasses$8;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextFieldIconFoundation, "defaultAdapter", {
          /**
           * See {@link MDCTextFieldIconAdapter} for typing information on parameters and return types.
           */
          get: function () {
              // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
              return {
                  getAttr: function () { return null; },
                  setAttr: function () { return undefined; },
                  removeAttr: function () { return undefined; },
                  setContent: function () { return undefined; },
                  registerInteractionHandler: function () { return undefined; },
                  deregisterInteractionHandler: function () { return undefined; },
                  notifyIconAction: function () { return undefined; },
              };
              // tslint:enable:object-literal-sort-keys
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldIconFoundation.prototype.init = function () {
          var _this = this;
          this.savedTabIndex_ = this.adapter.getAttr('tabindex');
          INTERACTION_EVENTS$1.forEach(function (evtType) {
              _this.adapter.registerInteractionHandler(evtType, _this.interactionHandler_);
          });
      };
      MDCTextFieldIconFoundation.prototype.destroy = function () {
          var _this = this;
          INTERACTION_EVENTS$1.forEach(function (evtType) {
              _this.adapter.deregisterInteractionHandler(evtType, _this.interactionHandler_);
          });
      };
      MDCTextFieldIconFoundation.prototype.setDisabled = function (disabled) {
          if (!this.savedTabIndex_) {
              return;
          }
          if (disabled) {
              this.adapter.setAttr('tabindex', '-1');
              this.adapter.removeAttr('role');
          }
          else {
              this.adapter.setAttr('tabindex', this.savedTabIndex_);
              this.adapter.setAttr('role', strings$6.ICON_ROLE);
          }
      };
      MDCTextFieldIconFoundation.prototype.setAriaLabel = function (label) {
          this.adapter.setAttr('aria-label', label);
      };
      MDCTextFieldIconFoundation.prototype.setContent = function (content) {
          this.adapter.setContent(content);
      };
      MDCTextFieldIconFoundation.prototype.handleInteraction = function (evt) {
          var isEnterKey = evt.key === 'Enter' || evt.keyCode === 13;
          if (evt.type === 'click' || isEnterKey) {
              evt.preventDefault(); // stop click from causing host label to focus
              // input
              this.adapter.notifyIconAction();
          }
      };
      return MDCTextFieldIconFoundation;
  }(MDCFoundation));

  /**
   * @license
   * Copyright 2017 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextFieldIcon = /** @class */ (function (_super) {
      __extends(MDCTextFieldIcon, _super);
      function MDCTextFieldIcon() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCTextFieldIcon.attachTo = function (root) {
          return new MDCTextFieldIcon(root);
      };
      Object.defineProperty(MDCTextFieldIcon.prototype, "foundationForTextField", {
          // Provided for access by MDCTextField component
          get: function () {
              return this.foundation;
          },
          enumerable: true,
          configurable: true
      });
      MDCTextFieldIcon.prototype.getDefaultFoundation = function () {
          var _this = this;
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = {
              getAttr: function (attr) { return _this.root.getAttribute(attr); },
              setAttr: function (attr, value) { return _this.root.setAttribute(attr, value); },
              removeAttr: function (attr) { return _this.root.removeAttribute(attr); },
              setContent: function (content) {
                  _this.root.textContent = content;
              },
              registerInteractionHandler: function (evtType, handler) { return _this.listen(evtType, handler); },
              deregisterInteractionHandler: function (evtType, handler) { return _this.unlisten(evtType, handler); },
              notifyIconAction: function () { return _this.emit(MDCTextFieldIconFoundation.strings.ICON_EVENT, {} /* evtData */, true /* shouldBubble */); },
          };
          // tslint:enable:object-literal-sort-keys
          return new MDCTextFieldIconFoundation(adapter);
      };
      return MDCTextFieldIcon;
  }(MDCComponent));

  /**
   * @license
   * Copyright 2016 Google Inc.
   *
   * Permission is hereby granted, free of charge, to any person obtaining a copy
   * of this software and associated documentation files (the "Software"), to deal
   * in the Software without restriction, including without limitation the rights
   * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   * copies of the Software, and to permit persons to whom the Software is
   * furnished to do so, subject to the following conditions:
   *
   * The above copyright notice and this permission notice shall be included in
   * all copies or substantial portions of the Software.
   *
   * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
   * THE SOFTWARE.
   */
  var MDCTextField = /** @class */ (function (_super) {
      __extends(MDCTextField, _super);
      function MDCTextField() {
          return _super !== null && _super.apply(this, arguments) || this;
      }
      MDCTextField.attachTo = function (root) {
          return new MDCTextField(root);
      };
      MDCTextField.prototype.initialize = function (rippleFactory, lineRippleFactory, helperTextFactory, characterCounterFactory, iconFactory, labelFactory, outlineFactory) {
          if (rippleFactory === void 0) { rippleFactory = function (el, foundation) { return new MDCRipple(el, foundation); }; }
          if (lineRippleFactory === void 0) { lineRippleFactory = function (el) { return new MDCLineRipple(el); }; }
          if (helperTextFactory === void 0) { helperTextFactory = function (el) { return new MDCTextFieldHelperText(el); }; }
          if (characterCounterFactory === void 0) { characterCounterFactory = function (el) { return new MDCTextFieldCharacterCounter(el); }; }
          if (iconFactory === void 0) { iconFactory = function (el) { return new MDCTextFieldIcon(el); }; }
          if (labelFactory === void 0) { labelFactory = function (el) { return new MDCFloatingLabel(el); }; }
          if (outlineFactory === void 0) { outlineFactory = function (el) { return new MDCNotchedOutline(el); }; }
          this.input_ = this.root.querySelector(strings$4.INPUT_SELECTOR);
          var labelElement = this.root.querySelector(strings$4.LABEL_SELECTOR);
          this.label_ = labelElement ? labelFactory(labelElement) : null;
          var lineRippleElement = this.root.querySelector(strings$4.LINE_RIPPLE_SELECTOR);
          this.lineRipple_ = lineRippleElement ? lineRippleFactory(lineRippleElement) : null;
          var outlineElement = this.root.querySelector(strings$4.OUTLINE_SELECTOR);
          this.outline_ = outlineElement ? outlineFactory(outlineElement) : null;
          // Helper text
          var helperTextStrings = MDCTextFieldHelperTextFoundation.strings;
          var nextElementSibling = this.root.nextElementSibling;
          var hasHelperLine = (nextElementSibling && nextElementSibling.classList.contains(cssClasses$6.HELPER_LINE));
          var helperTextEl = hasHelperLine && nextElementSibling && nextElementSibling.querySelector(helperTextStrings.ROOT_SELECTOR);
          this.helperText_ = helperTextEl ? helperTextFactory(helperTextEl) : null;
          // Character counter
          var characterCounterStrings = MDCTextFieldCharacterCounterFoundation.strings;
          var characterCounterEl = this.root.querySelector(characterCounterStrings.ROOT_SELECTOR);
          // If character counter is not found in root element search in sibling element.
          if (!characterCounterEl && hasHelperLine && nextElementSibling) {
              characterCounterEl = nextElementSibling.querySelector(characterCounterStrings.ROOT_SELECTOR);
          }
          this.characterCounter_ = characterCounterEl ? characterCounterFactory(characterCounterEl) : null;
          // Leading icon
          var leadingIconEl = this.root.querySelector(strings$4.LEADING_ICON_SELECTOR);
          this.leadingIcon_ = leadingIconEl ? iconFactory(leadingIconEl) : null;
          // Trailing icon
          var trailingIconEl = this.root.querySelector(strings$4.TRAILING_ICON_SELECTOR);
          this.trailingIcon_ = trailingIconEl ? iconFactory(trailingIconEl) : null;
          // Prefix and Suffix
          this.prefix_ = this.root.querySelector(strings$4.PREFIX_SELECTOR);
          this.suffix_ = this.root.querySelector(strings$4.SUFFIX_SELECTOR);
          this.ripple = this.createRipple_(rippleFactory);
      };
      MDCTextField.prototype.destroy = function () {
          if (this.ripple) {
              this.ripple.destroy();
          }
          if (this.lineRipple_) {
              this.lineRipple_.destroy();
          }
          if (this.helperText_) {
              this.helperText_.destroy();
          }
          if (this.characterCounter_) {
              this.characterCounter_.destroy();
          }
          if (this.leadingIcon_) {
              this.leadingIcon_.destroy();
          }
          if (this.trailingIcon_) {
              this.trailingIcon_.destroy();
          }
          if (this.label_) {
              this.label_.destroy();
          }
          if (this.outline_) {
              this.outline_.destroy();
          }
          _super.prototype.destroy.call(this);
      };
      /**
       * Initializes the Text Field's internal state based on the environment's
       * state.
       */
      MDCTextField.prototype.initialSyncWithDOM = function () {
          this.disabled = this.input_.disabled;
      };
      Object.defineProperty(MDCTextField.prototype, "value", {
          get: function () {
              return this.foundation.getValue();
          },
          /**
           * @param value The value to set on the input.
           */
          set: function (value) {
              this.foundation.setValue(value);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "disabled", {
          get: function () {
              return this.foundation.isDisabled();
          },
          /**
           * @param disabled Sets the Text Field disabled or enabled.
           */
          set: function (disabled) {
              this.foundation.setDisabled(disabled);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "valid", {
          get: function () {
              return this.foundation.isValid();
          },
          /**
           * @param valid Sets the Text Field valid or invalid.
           */
          set: function (valid) {
              this.foundation.setValid(valid);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "required", {
          get: function () {
              return this.input_.required;
          },
          /**
           * @param required Sets the Text Field to required.
           */
          set: function (required) {
              this.input_.required = required;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "pattern", {
          get: function () {
              return this.input_.pattern;
          },
          /**
           * @param pattern Sets the input element's validation pattern.
           */
          set: function (pattern) {
              this.input_.pattern = pattern;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "minLength", {
          get: function () {
              return this.input_.minLength;
          },
          /**
           * @param minLength Sets the input element's minLength.
           */
          set: function (minLength) {
              this.input_.minLength = minLength;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "maxLength", {
          get: function () {
              return this.input_.maxLength;
          },
          /**
           * @param maxLength Sets the input element's maxLength.
           */
          set: function (maxLength) {
              // Chrome throws exception if maxLength is set to a value less than zero
              if (maxLength < 0) {
                  this.input_.removeAttribute('maxLength');
              }
              else {
                  this.input_.maxLength = maxLength;
              }
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "min", {
          get: function () {
              return this.input_.min;
          },
          /**
           * @param min Sets the input element's min.
           */
          set: function (min) {
              this.input_.min = min;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "max", {
          get: function () {
              return this.input_.max;
          },
          /**
           * @param max Sets the input element's max.
           */
          set: function (max) {
              this.input_.max = max;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "step", {
          get: function () {
              return this.input_.step;
          },
          /**
           * @param step Sets the input element's step.
           */
          set: function (step) {
              this.input_.step = step;
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "helperTextContent", {
          /**
           * Sets the helper text element content.
           */
          set: function (content) {
              this.foundation.setHelperTextContent(content);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "leadingIconAriaLabel", {
          /**
           * Sets the aria label of the leading icon.
           */
          set: function (label) {
              this.foundation.setLeadingIconAriaLabel(label);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "leadingIconContent", {
          /**
           * Sets the text content of the leading icon.
           */
          set: function (content) {
              this.foundation.setLeadingIconContent(content);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "trailingIconAriaLabel", {
          /**
           * Sets the aria label of the trailing icon.
           */
          set: function (label) {
              this.foundation.setTrailingIconAriaLabel(label);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "trailingIconContent", {
          /**
           * Sets the text content of the trailing icon.
           */
          set: function (content) {
              this.foundation.setTrailingIconContent(content);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "useNativeValidation", {
          /**
           * Enables or disables the use of native validation. Use this for custom validation.
           * @param useNativeValidation Set this to false to ignore native input validation.
           */
          set: function (useNativeValidation) {
              this.foundation.setUseNativeValidation(useNativeValidation);
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "prefixText", {
          /**
           * Gets the text content of the prefix, or null if it does not exist.
           */
          get: function () {
              return this.prefix_ ? this.prefix_.textContent : null;
          },
          /**
           * Sets the text content of the prefix, if it exists.
           */
          set: function (prefixText) {
              if (this.prefix_) {
                  this.prefix_.textContent = prefixText;
              }
          },
          enumerable: true,
          configurable: true
      });
      Object.defineProperty(MDCTextField.prototype, "suffixText", {
          /**
           * Gets the text content of the suffix, or null if it does not exist.
           */
          get: function () {
              return this.suffix_ ? this.suffix_.textContent : null;
          },
          /**
           * Sets the text content of the suffix, if it exists.
           */
          set: function (suffixText) {
              if (this.suffix_) {
                  this.suffix_.textContent = suffixText;
              }
          },
          enumerable: true,
          configurable: true
      });
      /**
       * Focuses the input element.
       */
      MDCTextField.prototype.focus = function () {
          this.input_.focus();
      };
      /**
       * Recomputes the outline SVG path for the outline element.
       */
      MDCTextField.prototype.layout = function () {
          var openNotch = this.foundation.shouldFloat;
          this.foundation.notchOutline(openNotch);
      };
      MDCTextField.prototype.getDefaultFoundation = function () {
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = __assign(__assign(__assign(__assign(__assign({}, this.getRootAdapterMethods_()), this.getInputAdapterMethods_()), this.getLabelAdapterMethods_()), this.getLineRippleAdapterMethods_()), this.getOutlineAdapterMethods_());
          // tslint:enable:object-literal-sort-keys
          return new MDCTextFieldFoundation(adapter, this.getFoundationMap_());
      };
      MDCTextField.prototype.getRootAdapterMethods_ = function () {
          var _this = this;
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          return {
              addClass: function (className) { return _this.root.classList.add(className); },
              removeClass: function (className) { return _this.root.classList.remove(className); },
              hasClass: function (className) { return _this.root.classList.contains(className); },
              registerTextFieldInteractionHandler: function (evtType, handler) {
                  _this.listen(evtType, handler);
              },
              deregisterTextFieldInteractionHandler: function (evtType, handler) {
                  _this.unlisten(evtType, handler);
              },
              registerValidationAttributeChangeHandler: function (handler) {
                  var getAttributesList = function (mutationsList) {
                      return mutationsList
                          .map(function (mutation) { return mutation.attributeName; })
                          .filter(function (attributeName) { return attributeName; });
                  };
                  var observer = new MutationObserver(function (mutationsList) { return handler(getAttributesList(mutationsList)); });
                  var config = { attributes: true };
                  observer.observe(_this.input_, config);
                  return observer;
              },
              deregisterValidationAttributeChangeHandler: function (observer) {
                  observer.disconnect();
              },
          };
          // tslint:enable:object-literal-sort-keys
      };
      MDCTextField.prototype.getInputAdapterMethods_ = function () {
          var _this = this;
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          return {
              getNativeInput: function () { return _this.input_; },
              setInputAttr: function (attr, value) {
                  _this.input_.setAttribute(attr, value);
              },
              removeInputAttr: function (attr) {
                  _this.input_.removeAttribute(attr);
              },
              isFocused: function () { return document.activeElement === _this.input_; },
              registerInputInteractionHandler: function (evtType, handler) {
                  _this.input_.addEventListener(evtType, handler, applyPassive());
              },
              deregisterInputInteractionHandler: function (evtType, handler) {
                  _this.input_.removeEventListener(evtType, handler, applyPassive());
              },
          };
          // tslint:enable:object-literal-sort-keys
      };
      MDCTextField.prototype.getLabelAdapterMethods_ = function () {
          var _this = this;
          return {
              floatLabel: function (shouldFloat) { return _this.label_ && _this.label_.float(shouldFloat); },
              getLabelWidth: function () { return _this.label_ ? _this.label_.getWidth() : 0; },
              hasLabel: function () { return Boolean(_this.label_); },
              shakeLabel: function (shouldShake) { return _this.label_ && _this.label_.shake(shouldShake); },
              setLabelRequired: function (isRequired) { return _this.label_ && _this.label_.setRequired(isRequired); },
          };
      };
      MDCTextField.prototype.getLineRippleAdapterMethods_ = function () {
          var _this = this;
          return {
              activateLineRipple: function () {
                  if (_this.lineRipple_) {
                      _this.lineRipple_.activate();
                  }
              },
              deactivateLineRipple: function () {
                  if (_this.lineRipple_) {
                      _this.lineRipple_.deactivate();
                  }
              },
              setLineRippleTransformOrigin: function (normalizedX) {
                  if (_this.lineRipple_) {
                      _this.lineRipple_.setRippleCenter(normalizedX);
                  }
              },
          };
      };
      MDCTextField.prototype.getOutlineAdapterMethods_ = function () {
          var _this = this;
          return {
              closeOutline: function () { return _this.outline_ && _this.outline_.closeNotch(); },
              hasOutline: function () { return Boolean(_this.outline_); },
              notchOutline: function (labelWidth) { return _this.outline_ && _this.outline_.notch(labelWidth); },
          };
      };
      /**
       * @return A map of all subcomponents to subfoundations.
       */
      MDCTextField.prototype.getFoundationMap_ = function () {
          return {
              characterCounter: this.characterCounter_ ?
                  this.characterCounter_.foundationForTextField :
                  undefined,
              helperText: this.helperText_ ? this.helperText_.foundationForTextField :
                  undefined,
              leadingIcon: this.leadingIcon_ ?
                  this.leadingIcon_.foundationForTextField :
                  undefined,
              trailingIcon: this.trailingIcon_ ?
                  this.trailingIcon_.foundationForTextField :
                  undefined,
          };
      };
      MDCTextField.prototype.createRipple_ = function (rippleFactory) {
          var _this = this;
          var isTextArea = this.root.classList.contains(cssClasses$6.TEXTAREA);
          var isOutlined = this.root.classList.contains(cssClasses$6.OUTLINED);
          if (isTextArea || isOutlined) {
              return null;
          }
          // DO NOT INLINE this variable. For backward compatibility, foundations take a Partial<MDCFooAdapter>.
          // To ensure we don't accidentally omit any methods, we need a separate, strongly typed adapter variable.
          // tslint:disable:object-literal-sort-keys Methods should be in the same order as the adapter interface.
          var adapter = __assign(__assign({}, MDCRipple.createAdapter(this)), { isSurfaceActive: function () { return matches(_this.input_, ':active'); }, registerInteractionHandler: function (evtType, handler) { return _this.input_.addEventListener(evtType, handler, applyPassive()); }, deregisterInteractionHandler: function (evtType, handler) {
                  return _this.input_.removeEventListener(evtType, handler, applyPassive());
              } });
          // tslint:enable:object-literal-sort-keys
          return rippleFactory(this.root, new MDCRippleFoundation(adapter));
      };
      return MDCTextField;
  }(MDCComponent));

  const _tmpl$$1 = template(`<div class="mdc-text-field-helper-line"><div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent"></div></div>`, 4),
        _tmpl$2$1 = template(`<label><span class="mdc-notched-outline"><span class="mdc-notched-outline__leading"></span><span class="mdc-notched-outline__notch"></span><span class="mdc-notched-outline__trailing"></span></span><input class="mdc-text-field__input"></label>`, 11),
        _tmpl$3 = template(`<span></span>`, 2),
        _tmpl$4 = template(`<i class="material-icons mdc-text-field__icon mdc-text-field__icon--leading" tabindex="-1" role="button"></i>`, 2),
        _tmpl$5 = template(`<div class="mdc-touch-target-wrapper"><button class="mdc-button vf-text-field__button mdc-button--touch" type="button"><div class="mdc-button__ripple"></div><span class="mdc-button__label material-icons"></span><div class="mdc-button__touch"></div></button></div>`, 10),
        _tmpl$6 = template(`<i class="material-icons mdc-text-field__icon mdc-text-field__icon--trailing" tabindex="-1" role="button"></i>`, 2),
        _tmpl$7 = template(`<div class="vf-field__row"></div>`, 2);
  const defaultProps$1 = {
    'autofocus': undefined,
    'disabled': false,
    'error': undefined,
    'helpText': undefined,
    'id': undefined,
    'label': undefined,
    'leadingIcon': undefined,
    'maxlength': undefined,
    'minlength': undefined,
    'name': undefined,
    'placeholder': undefined,
    'required': false,
    'step': undefined,
    'trailingIcon': undefined,
    'type': 'text',
    'value': undefined
  };
  const HelpText = props => {
    return (() => {
      const _el$ = _tmpl$$1.cloneNode(true),
            _el$2 = _el$.firstChild;

      insert(_el$2, () => props.error || props.helpText);

      return _el$;
    })();
  };
  const Input = props => {
    let control;
    let textfield;
    afterEffects(() => {
      setTimeout(() => {
        textfield = new MDCTextField(control);
        control.textfield = textfield;
      });
    });
    onCleanup(() => {
      textfield.destroy();
    });
    return (() => {
      const _el$3 = _tmpl$2$1.cloneNode(true),
            _el$4 = _el$3.firstChild,
            _el$5 = _el$4.firstChild,
            _el$6 = _el$5.nextSibling,
            _el$7 = _el$4.nextSibling;

      typeof control === "function" ? control(_el$3) : control = _el$3;

      insert(_el$6, (() => {
        const _c$ = memo(() => !!props.label, true);

        return () => _c$() ? (() => {
          const _el$8 = _tmpl$3.cloneNode(true);

          insert(_el$8, () => props.label);

          createEffect(_p$ => {
            const _v$15 = cc({
              'mdc-floating-label': true,
              'mdc-floating-label--float-above': props.value !== undefined,
              'mdc-floating-label--required': props.required
            }),
                  _v$16 = props.id + '_label';

            _v$15 !== _p$._v$15 && (_el$8.className = _p$._v$15 = _v$15);
            _v$16 !== _p$._v$16 && (_el$8.id = _p$._v$16 = _v$16);
            return _p$;
          }, {
            _v$15: undefined,
            _v$16: undefined
          });

          return _el$8;
        })() : '';
      })());

      insert(_el$3, (() => {
        const _c$ = memo(() => !!props.leadingIcon, true);

        return () => _c$() ? (() => {
          const _el$9 = _tmpl$4.cloneNode(true);

          insert(_el$9, () => props.leadingIcon);

          return _el$9;
        })() : '';
      })(), _el$7);

      _el$7.__keydown = props.onKeyDown;
      _el$7.__keyup = props.onKeyUp;
      _el$7.onfocus = props.onFocus;
      _el$7.onchange = props.onChange;

      insert(_el$3, (() => {
        const _c$ = memo(() => !!props.trailingButton, true);

        return () => _c$() ? (() => {
          const _el$10 = _tmpl$5.cloneNode(true),
                _el$11 = _el$10.firstChild,
                _el$12 = _el$11.firstChild,
                _el$13 = _el$12.nextSibling;

          _el$11.__click = props.onTrailingButtonClick;

          insert(_el$13, () => props.trailingButton);

          createEffect(() => _el$11.disabled = props.disabled);

          return _el$10;
        })() : (() => {
          const _c$ = memo(() => !!props.trailingIcon, true);

          return () => _c$() ? (() => {
            const _el$14 = _tmpl$6.cloneNode(true);

            insert(_el$14, () => props.trailingIcon);

            return _el$14;
          })() : '';
        })();
      })(), null);

      createEffect(_p$ => {
        const _v$ = cc({
          'mdc-text-field': true,
          'mdc-text-field--outlined': true,
          'mdc-text-field--invalid': !!props.error,
          'mdc-text-field--with-leading-icon': !!props.leadingIcon,
          'mdc-text-field--with-trailing-icon': !!props.trailingIcon
        }),
              _v$2 = !!props.autofocus,
              _v$3 = props.autocomplete,
              _v$4 = !!props.disabled,
              _v$5 = props.id + '_control',
              _v$6 = props.maxlength,
              _v$7 = props.minlength,
              _v$8 = props.name,
              _v$9 = props.placeholder,
              _v$10 = !!props.required,
              _v$11 = props.step,
              _v$12 = props.type,
              _v$13 = props.value,
              _v$14 = props.id + '_label';

        _v$ !== _p$._v$ && (_el$3.className = _p$._v$ = _v$);
        _v$2 !== _p$._v$2 && (_el$7.autofocus = _p$._v$2 = _v$2);
        _v$3 !== _p$._v$3 && (_el$7.autocomplete = _p$._v$3 = _v$3);
        _v$4 !== _p$._v$4 && (_el$7.disabled = _p$._v$4 = _v$4);
        _v$5 !== _p$._v$5 && (_el$7.id = _p$._v$5 = _v$5);
        _v$6 !== _p$._v$6 && (_el$7.maxlength = _p$._v$6 = _v$6);
        _v$7 !== _p$._v$7 && (_el$7.minlength = _p$._v$7 = _v$7);
        _v$8 !== _p$._v$8 && (_el$7.name = _p$._v$8 = _v$8);
        _v$9 !== _p$._v$9 && (_el$7.placeholder = _p$._v$9 = _v$9);
        _v$10 !== _p$._v$10 && (_el$7.required = _p$._v$10 = _v$10);
        _v$11 !== _p$._v$11 && (_el$7.step = _p$._v$11 = _v$11);
        _v$12 !== _p$._v$12 && (_el$7.type = _p$._v$12 = _v$12);
        _v$13 !== _p$._v$13 && (_el$7.value = _p$._v$13 = _v$13);
        _v$14 !== _p$._v$14 && setAttribute(_el$7, "aria-labelledby", _p$._v$14 = _v$14);
        return _p$;
      }, {
        _v$: undefined,
        _v$2: undefined,
        _v$3: undefined,
        _v$4: undefined,
        _v$5: undefined,
        _v$6: undefined,
        _v$7: undefined,
        _v$8: undefined,
        _v$9: undefined,
        _v$10: undefined,
        _v$11: undefined,
        _v$12: undefined,
        _v$13: undefined,
        _v$14: undefined
      });

      return _el$3;
    })();
  };
  const VInputField = customElement('vf-field-input', defaultProps$1, (props, {
    element
  }) => {
    noShadowDOM();
    return (() => {
      const _el$15 = _tmpl$7.cloneNode(true);

      insert(_el$15, createComponent(Input, Object.assign(Object.keys(props).reduce((m$, k$) => (m$[k$] = () => props[k$], m$), {}), {}), Object.keys(props)), null);

      insert(_el$15, (() => {
        const _c$ = memo(() => !!(props.helpText || props.error), true);

        return () => _c$() ? createComponent(HelpText, Object.assign(Object.keys(props).reduce((m$, k$) => (m$[k$] = () => props[k$], m$), {}), {}), Object.keys(props)) : '';
      })(), null);

      return _el$15;
    })();
  });

  delegateEvents(["keyup", "keydown", "click"]);

  const _tmpl$$2 = template(`<div class="vf-field__row"></div>`, 2);
  const defaultProps$2 = {
    'autofocus': undefined,
    'disabled': false,
    'error': undefined,
    'helpText': undefined,
    'id': undefined,
    'label': undefined,
    'leadingIcon': undefined,
    'maxlength': undefined,
    'minlength': undefined,
    'name': undefined,
    'placeholder': undefined,
    'required': false,
    'type': 'password',
    'value': undefined
  };
  const VPasswordField = customElement('vf-field-password', defaultProps$2, (props, {
    element
  }) => {
    const [state, setState] = createState({
      'visible': props.type !== 'password'
    });
    noShadowDOM();

    const onBtnClick = event => {
      event.preventDefault();
      setState({
        'visible': !state.visible
      });
    };

    return (() => {
      const _el$ = _tmpl$$2.cloneNode(true);

      insert(_el$, createComponent(Input, Object.assign(Object.keys(props).reduce((m$, k$) => (m$[k$] = () => props[k$], m$), {}), {
        type: () => state.visible ? 'text' : 'password',
        trailingButton: () => state.visible ? 'visibility' : 'visibility_off',
        onTrailingButtonClick: onBtnClick
      }), Object.keys(props)), null);

      insert(_el$, (() => {
        const _c$ = memo(() => !!(props.helpText || props.error), true);

        return () => _c$() ? createComponent(HelpText, Object.assign(Object.keys(props).reduce((m$, k$) => (m$[k$] = () => props[k$], m$), {}), {}), Object.keys(props)) : '';
      })(), null);

      return _el$;
    })();
  });

  const _tmpl$$3 = template(`<div class="mdc-form-field"><div><input class="mdc-radio__native-control" type="radio"><div class="mdc-radio__background"><div class="mdc-radio__outer-circle"></div><div class="mdc-radio__inner-circle"></div></div><div class="mdc-radio__ripple"></div></div><label></label></div>`, 15),
        _tmpl$2$2 = template(`<div><label class="vf-radio-select__label mdc-floating-label"></label><div class="vf-radio-select__control"></div></div>`, 6),
        _tmpl$3$1 = template(`<div class="mdc-text-field-helper-line"><div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent"></div></div>`, 4);
  const defaultProps$3 = {
    'disabled': false,
    'error': undefined,
    'helpText': undefined,
    'id': undefined,
    'inline': undefined,
    'label': undefined,
    'name': undefined,
    'optgroups': undefined,
    'required': false,
    'value': undefined
  };
  const VRadioSelectField = customElement('vf-field-radio-select', defaultProps$3, (props, {
    element
  }) => {
    noShadowDOM();

    const items = props => {
      const items = [];

      for (const groupData of props.optgroups) {
        items.push((() => {
          const _el$ = _tmpl$$3.cloneNode(true),
                _el$2 = _el$.firstChild,
                _el$3 = _el$2.firstChild,
                _el$4 = _el$2.nextSibling;

          spread(_el$3, () => groupData.options.attrs, false, false);

          insert(_el$4, () => groupData.options.label);

          createEffect(_p$ => {
            const _v$ = cc({
              'mdc-radio': true,
              'mdc-radio--disabled': !!props.disabled
            }),
                  _v$2 = groupData.options.selected,
                  _v$3 = !!props.disabled,
                  _v$4 = groupData.options.name,
                  _v$5 = groupData.options.value,
                  _v$6 = groupData.options.attrs.id;

            _v$ !== _p$._v$ && (_el$2.className = _p$._v$ = _v$);
            _v$2 !== _p$._v$2 && (_el$3.checked = _p$._v$2 = _v$2);
            _v$3 !== _p$._v$3 && (_el$3.disabled = _p$._v$3 = _v$3);
            _v$4 !== _p$._v$4 && (_el$3.name = _p$._v$4 = _v$4);
            _v$5 !== _p$._v$5 && (_el$3.value = _p$._v$5 = _v$5);
            _v$6 !== _p$._v$6 && (_el$4.htmlFor = _p$._v$6 = _v$6);
            return _p$;
          }, {
            _v$: undefined,
            _v$2: undefined,
            _v$3: undefined,
            _v$4: undefined,
            _v$5: undefined,
            _v$6: undefined
          });

          return _el$;
        })());
      }

      return items;
    };

    return (() => {
      const _el$5 = _tmpl$2$2.cloneNode(true),
            _el$6 = _el$5.firstChild,
            _el$7 = _el$6.nextSibling;

      insert(_el$6, () => props.label);

      insert(_el$7, () => items(props));

      insert(_el$5, (() => {
        const _c$ = memo(() => !!(props.helpText || props.error), true);

        return () => _c$() ? (() => {
          const _el$8 = _tmpl$3$1.cloneNode(true),
                _el$9 = _el$8.firstChild;

          insert(_el$9, () => props.error || props.helpText);

          return _el$8;
        })() : '';
      })(), null);

      createEffect(() => _el$5.className = cc({
        'vf-field__row': true,
        'vf-radio--inline': !!props.inline,
        'vf-radio--invalid': !!props.error
      }));

      return _el$5;
    })();
  });

  function _defineProperty(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
  class VCardMenu extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty(this, "onToggleMenu", () => {
        this._mdcMenu.open = !this._mdcMenu.open;
      });

      _defineProperty(this, "onMenuSelect", event => {
        event.preventDefault();
        const itemData = event.detail.item.dataset;

        if (itemData.cardMenuHref) {
          if (Turbolinks__default['default']) {
            Turbolinks__default['default'].visit(itemData.cardMenuHref);
          } else {
            window.location = itemData.cardMenuHref;
          }
        }
      });
    }

    connectedCallback() {
      setTimeout(() => {
        this._menuEl = this.querySelector('.mdc-menu');
        this._triggerEl = this.querySelector('.vf-card__menu-trigger');
        this._mdcMenu = new materialComponentsWeb.menu.MDCMenu(this._menuEl);

        this._menuEl.addEventListener('MDCMenu:selected', this.onMenuSelect);

        this._triggerEl.addEventListener('click', this.onToggleMenu);
      });
    }

    disconnectedCallback() {
      this._mdcMenu.destroy();

      this._triggerEl.removeEventListener('click', this.onToggleMenu);
    }

  }

  /* eslint-env browser */
  class DOMBuilder {
    constructor(tagName, attrs) {
      this.tagName = tagName;
      this.attrs = attrs;
      this.content = null;
      this.textContent = null;
    }

    with(content) {
      if (!(content instanceof Array)) {
        content = [content];
      }

      this.content = content;
      return this;
    }

    text(textContent) {
      this.textContent = textContent;
      return this;
    }

    _createElement(tagName) {
      return document.createElement(tagName);
    }

    _setAttribute(element, attr, value) {
      element.setAttribute(attr, value);
    }

    toDOM() {
      const element = this._createElement(this.tagName);

      if (this.textContent) {
        element.textContent = this.textContent;
      }

      for (let attr in this.attrs) {
        if (this.attrs.hasOwnProperty(attr)) {
          let value = this.attrs[attr];

          if (value === undefined || value === null) {
            // skip undefined values
            continue;
          } else if (value instanceof Array) {
            // join array data
            value = value.join(' ');
          } else if (typeof value === 'boolean') {
            if (value === false) {
              // skip false boolean attributes
              continue;
            } else {
              value = '';
            }
          } else if (!(typeof value === 'string' || typeof value === 'number')) {
            // join hash key if enabled
            let valuesList = [];

            for (let key in value) {
              if (value.hasOwnProperty(key)) {
                const keyValue = value[key];

                if (keyValue) {
                  valuesList.push(key);
                }
              }
            }

            value = valuesList.join(' ');
          }

          this._setAttribute(element, attr, value == null ? '' : value);
        }
      }

      if (this.content) {
        for (let i = 0; i < this.content.length; i++) {
          const child = this.content[i];

          if (child) {
            if (child instanceof DOMBuilder) {
              element.appendChild(child.toDOM());
            } else {
              element.appendChild(document.createTextNode(child));
            }
          }
        }
      }

      return element;
    }

  }
  function div(attrs) {
    return new DOMBuilder('div', attrs);
  }
  function a(attrs) {
    return new DOMBuilder('a', attrs);
  }

  function _defineProperty$1(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
  class VPage extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$1(this, "onWindowResize", () => {
        cancelAnimationFrame(this._reconcileDrawerFrame);
        this._reconcileDrawerFrame = requestAnimationFrame(() => this.reconcileDrawer());
      });

      _defineProperty$1(this, "onToggleMenuClick", event => {
        event.preventDefault();
        this.classList.toggle('vf-page__menu--secondary-open');
      });
    }

    connectedCallback() {
      this._reconcileDrawerFrame = 0;
      this._mdcDrawer = null;
      this._topAppBar = null;
      this._drawerEl = this.querySelector('.vf-page__menu');
      this._contentEl = this.querySelector('.vf-page__body');
      this._toggleMenuEl = this.querySelector('.vf-page__menu-toggle-button');
      this._topAppBarEl = this.querySelector('.vf-page__body-toolbar');
      this._scrimEl = div({
        class: 'mdc-drawer-scrim'
      }).toDOM();

      if (window.innerWidth >= 992) {
        this._drawerEl.classList.toggle('mdc-drawer--open', sessionStorage.getItem('viewflow_site_drawer_state') != 'closed');
      }

      this._toggleMenuEl.addEventListener('click', this.onToggleMenuClick);

      window.addEventListener('resize', this.onWindowResize);
      this._mdcDrawer = materialComponentsWeb.drawer.MDCDrawer.attachTo(this._drawerEl);
      this._topAppBar = materialComponentsWeb.topAppBar.MDCTopAppBar.attachTo(this._topAppBarEl);

      this._topAppBar.setScrollTarget(this.querySelector('.vf-page__content'));

      this._topAppBar.listen('MDCTopAppBar:nav', event => {
        event.preventDefault();
        this.open = !this.open;
      });

      this.reconcileDrawer();
    }

    disconnectedCallback() {
      window.removeEventListener('resize', this.onWindowResize);

      this._toggleMenuEl.removeEventListener('click', this.onToggleMenuClick);

      if (this._mdcDrawer) {
        this._mdcDrawer.destroy();
      }

      if (this._topAppBar) {
        this._topAppBar.destroy();
      }
    }

    reconcileDrawer() {
      const rootClasses = this._drawerEl.classList;

      if (window.innerWidth < 992 && !rootClasses.contains('mdc-drawer--modal')) {
        this._mdcDrawer.destroy();

        this._drawerEl.classList.remove('mdc-drawer--dismissible');

        this._drawerEl.classList.remove('mdc-drawer--open');

        this._drawerEl.classList.add('mdc-drawer--modal');

        this.insertBefore(this._scrimEl, this._contentEl);

        this._contentEl.classList.remove('mdc-drawer-app-content');

        this._mdcDrawer = materialComponentsWeb.drawer.MDCDrawer.attachTo(this._drawerEl);
      } else if (window.innerWidth >= 992 && !rootClasses.contains('mdc-drawer--dismissible')) {
        this._mdcDrawer.destroy();

        this._drawerEl.classList.remove('mdc-drawer--modal');

        this._scrimEl.remove();

        this._drawerEl.classList.add('mdc-drawer--dismissible');

        this._contentEl.classList.add('mdc-drawer-app-content');

        this._drawerEl.classList.toggle('mdc-drawer--open', sessionStorage.getItem('viewflow_site_drawer_state') != 'closed');

        this._mdcDrawer = materialComponentsWeb.drawer.MDCDrawer.attachTo(this._drawerEl);
      }
    }

    get open() {
      if (this._mdcDrawer) {
        return this._mdcDrawer.open;
      }
    }

    set open(value) {
      if (this._mdcDrawer) {
        if (window.innerWidth >= 992) {
          sessionStorage.setItem('viewflow_site_drawer_state', value ? 'open' : 'closed');
        }

        return this._mdcDrawer.open = value;
      }
    }

  }
  class VPageMenuToggle extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$1(this, "onClick", event => {
        event.preventDefault();
        this._pageMenu.open = !this._pageMenu.open;
      });
    }

    connectedCallback() {
      setTimeout(() => {
        this._pageMenu = document.querySelector('vf-page-menu');
        this.addEventListener('click', this.onClick);
      });
    }

    disconnectedCallback() {
      this.removeEventListener('click', this.onClick);
    }

  }
  class VPageMenuNavigation extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$1(this, "activate", () => {
        let currentPath = window.location.pathname;

        if (Turbolinks__default['default'].controller.currentVisit && Turbolinks__default['default'].controller.currentVisit.redirectedToLocation) {
          currentPath = Turbolinks__default['default'].controller.currentVisit.redirectedToLocation.absoluteURL.substring(window.location.origin.length);
        }

        const navItems = [].slice.call(this.querySelectorAll('.mdc-list-item:not(.vf-page-navigation__ignore)')).filter(node => currentPath.startsWith(node.pathname));
        navItems.sort((a, b) => b.pathname.length - a.pathname.length);

        if (navItems.length) {
          navItems[0].classList.add('mdc-list-item--selected');
        }
      });
    }

    connectedCallback() {
      if (this.children.length) {
        this.activate();
      } else {
        setTimeout(this.activate);
      }
    }

  }
  class VPageScrollFix extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$1(this, "onResize", () => {
        if (!document.body.style.width) {
          this._clientWidth = document.body.clientWidth;
        } else {
          cancelAnimationFrame(this._reconcileBodyFrame);
          this._reconcileBodyFrame = requestAnimationFrame(() => {
            document.body.style.width = window.innerWidth - this._gap + 'px';
          });
        }
      });

      _defineProperty$1(this, "onBodyChanged", mutationsList => {
        const overflow = window.getComputedStyle(document.body).overflow;

        if (overflow == 'hidden') {
          this._gap = window.innerWidth - this._clientWidth;
          document.body.style.width = this._clientWidth + 'px';
        } else {
          document.body.style.removeProperty('width');
          this._clientWidth = document.body.clientWidth;
        }
      });
    }

    connectedCallback() {
      this._reconcileBodyFrame = 0;
      this._clientWidth = document.body.clientWidth;
      this._gap = 0;
      window.addEventListener('resize', this.onResize);
      this._observer = new MutationObserver(this.onBodyChanged);

      this._observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['class']
      });
    }

    disconnectedCallback() {
      window.removeEventListener('resize', this.onResize);
      cancelAnimationFrame(this._reconcileBodyFrame);

      this._observer.disconnect();
    }

  }

  /*!
   * perfect-scrollbar v1.5.0
   * Copyright 2020 Hyunje Jun, MDBootstrap and Contributors
   * Licensed under MIT
   */

  function get(element) {
    return getComputedStyle(element);
  }

  function set(element, obj) {
    for (var key in obj) {
      var val = obj[key];
      if (typeof val === 'number') {
        val = val + "px";
      }
      element.style[key] = val;
    }
    return element;
  }

  function div$1(className) {
    var div = document.createElement('div');
    div.className = className;
    return div;
  }

  var elMatches =
    typeof Element !== 'undefined' &&
    (Element.prototype.matches ||
      Element.prototype.webkitMatchesSelector ||
      Element.prototype.mozMatchesSelector ||
      Element.prototype.msMatchesSelector);

  function matches$1(element, query) {
    if (!elMatches) {
      throw new Error('No element matching method supported');
    }

    return elMatches.call(element, query);
  }

  function remove(element) {
    if (element.remove) {
      element.remove();
    } else {
      if (element.parentNode) {
        element.parentNode.removeChild(element);
      }
    }
  }

  function queryChildren(element, selector) {
    return Array.prototype.filter.call(element.children, function (child) { return matches$1(child, selector); }
    );
  }

  var cls = {
    main: 'ps',
    rtl: 'ps__rtl',
    element: {
      thumb: function (x) { return ("ps__thumb-" + x); },
      rail: function (x) { return ("ps__rail-" + x); },
      consuming: 'ps__child--consume',
    },
    state: {
      focus: 'ps--focus',
      clicking: 'ps--clicking',
      active: function (x) { return ("ps--active-" + x); },
      scrolling: function (x) { return ("ps--scrolling-" + x); },
    },
  };

  /*
   * Helper methods
   */
  var scrollingClassTimeout = { x: null, y: null };

  function addScrollingClass(i, x) {
    var classList = i.element.classList;
    var className = cls.state.scrolling(x);

    if (classList.contains(className)) {
      clearTimeout(scrollingClassTimeout[x]);
    } else {
      classList.add(className);
    }
  }

  function removeScrollingClass(i, x) {
    scrollingClassTimeout[x] = setTimeout(
      function () { return i.isAlive && i.element.classList.remove(cls.state.scrolling(x)); },
      i.settings.scrollingThreshold
    );
  }

  function setScrollingClassInstantly(i, x) {
    addScrollingClass(i, x);
    removeScrollingClass(i, x);
  }

  var EventElement = function EventElement(element) {
    this.element = element;
    this.handlers = {};
  };

  var prototypeAccessors = { isEmpty: { configurable: true } };

  EventElement.prototype.bind = function bind (eventName, handler) {
    if (typeof this.handlers[eventName] === 'undefined') {
      this.handlers[eventName] = [];
    }
    this.handlers[eventName].push(handler);
    this.element.addEventListener(eventName, handler, false);
  };

  EventElement.prototype.unbind = function unbind (eventName, target) {
      var this$1 = this;

    this.handlers[eventName] = this.handlers[eventName].filter(function (handler) {
      if (target && handler !== target) {
        return true;
      }
      this$1.element.removeEventListener(eventName, handler, false);
      return false;
    });
  };

  EventElement.prototype.unbindAll = function unbindAll () {
    for (var name in this.handlers) {
      this.unbind(name);
    }
  };

  prototypeAccessors.isEmpty.get = function () {
      var this$1 = this;

    return Object.keys(this.handlers).every(
      function (key) { return this$1.handlers[key].length === 0; }
    );
  };

  Object.defineProperties( EventElement.prototype, prototypeAccessors );

  var EventManager = function EventManager() {
    this.eventElements = [];
  };

  EventManager.prototype.eventElement = function eventElement (element) {
    var ee = this.eventElements.filter(function (ee) { return ee.element === element; })[0];
    if (!ee) {
      ee = new EventElement(element);
      this.eventElements.push(ee);
    }
    return ee;
  };

  EventManager.prototype.bind = function bind (element, eventName, handler) {
    this.eventElement(element).bind(eventName, handler);
  };

  EventManager.prototype.unbind = function unbind (element, eventName, handler) {
    var ee = this.eventElement(element);
    ee.unbind(eventName, handler);

    if (ee.isEmpty) {
      // remove
      this.eventElements.splice(this.eventElements.indexOf(ee), 1);
    }
  };

  EventManager.prototype.unbindAll = function unbindAll () {
    this.eventElements.forEach(function (e) { return e.unbindAll(); });
    this.eventElements = [];
  };

  EventManager.prototype.once = function once (element, eventName, handler) {
    var ee = this.eventElement(element);
    var onceHandler = function (evt) {
      ee.unbind(eventName, onceHandler);
      handler(evt);
    };
    ee.bind(eventName, onceHandler);
  };

  function createEvent(name) {
    if (typeof window.CustomEvent === 'function') {
      return new CustomEvent(name);
    } else {
      var evt = document.createEvent('CustomEvent');
      evt.initCustomEvent(name, false, false, undefined);
      return evt;
    }
  }

  function processScrollDiff(
    i,
    axis,
    diff,
    useScrollingClass,
    forceFireReachEvent
  ) {
    if ( useScrollingClass === void 0 ) useScrollingClass = true;
    if ( forceFireReachEvent === void 0 ) forceFireReachEvent = false;

    var fields;
    if (axis === 'top') {
      fields = [
        'contentHeight',
        'containerHeight',
        'scrollTop',
        'y',
        'up',
        'down' ];
    } else if (axis === 'left') {
      fields = [
        'contentWidth',
        'containerWidth',
        'scrollLeft',
        'x',
        'left',
        'right' ];
    } else {
      throw new Error('A proper axis should be provided');
    }

    processScrollDiff$1(i, diff, fields, useScrollingClass, forceFireReachEvent);
  }

  function processScrollDiff$1(
    i,
    diff,
    ref,
    useScrollingClass,
    forceFireReachEvent
  ) {
    var contentHeight = ref[0];
    var containerHeight = ref[1];
    var scrollTop = ref[2];
    var y = ref[3];
    var up = ref[4];
    var down = ref[5];
    if ( useScrollingClass === void 0 ) useScrollingClass = true;
    if ( forceFireReachEvent === void 0 ) forceFireReachEvent = false;

    var element = i.element;

    // reset reach
    i.reach[y] = null;

    // 1 for subpixel rounding
    if (element[scrollTop] < 1) {
      i.reach[y] = 'start';
    }

    // 1 for subpixel rounding
    if (element[scrollTop] > i[contentHeight] - i[containerHeight] - 1) {
      i.reach[y] = 'end';
    }

    if (diff) {
      element.dispatchEvent(createEvent(("ps-scroll-" + y)));

      if (diff < 0) {
        element.dispatchEvent(createEvent(("ps-scroll-" + up)));
      } else if (diff > 0) {
        element.dispatchEvent(createEvent(("ps-scroll-" + down)));
      }

      if (useScrollingClass) {
        setScrollingClassInstantly(i, y);
      }
    }

    if (i.reach[y] && (diff || forceFireReachEvent)) {
      element.dispatchEvent(createEvent(("ps-" + y + "-reach-" + (i.reach[y]))));
    }
  }

  function toInt(x) {
    return parseInt(x, 10) || 0;
  }

  function isEditable(el) {
    return (
      matches$1(el, 'input,[contenteditable]') ||
      matches$1(el, 'select,[contenteditable]') ||
      matches$1(el, 'textarea,[contenteditable]') ||
      matches$1(el, 'button,[contenteditable]')
    );
  }

  function outerWidth(element) {
    var styles = get(element);
    return (
      toInt(styles.width) +
      toInt(styles.paddingLeft) +
      toInt(styles.paddingRight) +
      toInt(styles.borderLeftWidth) +
      toInt(styles.borderRightWidth)
    );
  }

  var env = {
    isWebKit:
      typeof document !== 'undefined' &&
      'WebkitAppearance' in document.documentElement.style,
    supportsTouch:
      typeof window !== 'undefined' &&
      ('ontouchstart' in window ||
        ('maxTouchPoints' in window.navigator &&
          window.navigator.maxTouchPoints > 0) ||
        (window.DocumentTouch && document instanceof window.DocumentTouch)),
    supportsIePointer:
      typeof navigator !== 'undefined' && navigator.msMaxTouchPoints,
    isChrome:
      typeof navigator !== 'undefined' &&
      /Chrome/i.test(navigator && navigator.userAgent),
  };

  function updateGeometry(i) {
    var element = i.element;
    var roundedScrollTop = Math.floor(element.scrollTop);
    var rect = element.getBoundingClientRect();

    i.containerWidth = Math.ceil(rect.width);
    i.containerHeight = Math.ceil(rect.height);
    i.contentWidth = element.scrollWidth;
    i.contentHeight = element.scrollHeight;

    if (!element.contains(i.scrollbarXRail)) {
      // clean up and append
      queryChildren(element, cls.element.rail('x')).forEach(function (el) { return remove(el); }
      );
      element.appendChild(i.scrollbarXRail);
    }
    if (!element.contains(i.scrollbarYRail)) {
      // clean up and append
      queryChildren(element, cls.element.rail('y')).forEach(function (el) { return remove(el); }
      );
      element.appendChild(i.scrollbarYRail);
    }

    if (
      !i.settings.suppressScrollX &&
      i.containerWidth + i.settings.scrollXMarginOffset < i.contentWidth
    ) {
      i.scrollbarXActive = true;
      i.railXWidth = i.containerWidth - i.railXMarginWidth;
      i.railXRatio = i.containerWidth / i.railXWidth;
      i.scrollbarXWidth = getThumbSize(
        i,
        toInt((i.railXWidth * i.containerWidth) / i.contentWidth)
      );
      i.scrollbarXLeft = toInt(
        ((i.negativeScrollAdjustment + element.scrollLeft) *
          (i.railXWidth - i.scrollbarXWidth)) /
          (i.contentWidth - i.containerWidth)
      );
    } else {
      i.scrollbarXActive = false;
    }

    if (
      !i.settings.suppressScrollY &&
      i.containerHeight + i.settings.scrollYMarginOffset < i.contentHeight
    ) {
      i.scrollbarYActive = true;
      i.railYHeight = i.containerHeight - i.railYMarginHeight;
      i.railYRatio = i.containerHeight / i.railYHeight;
      i.scrollbarYHeight = getThumbSize(
        i,
        toInt((i.railYHeight * i.containerHeight) / i.contentHeight)
      );
      i.scrollbarYTop = toInt(
        (roundedScrollTop * (i.railYHeight - i.scrollbarYHeight)) /
          (i.contentHeight - i.containerHeight)
      );
    } else {
      i.scrollbarYActive = false;
    }

    if (i.scrollbarXLeft >= i.railXWidth - i.scrollbarXWidth) {
      i.scrollbarXLeft = i.railXWidth - i.scrollbarXWidth;
    }
    if (i.scrollbarYTop >= i.railYHeight - i.scrollbarYHeight) {
      i.scrollbarYTop = i.railYHeight - i.scrollbarYHeight;
    }

    updateCss(element, i);

    if (i.scrollbarXActive) {
      element.classList.add(cls.state.active('x'));
    } else {
      element.classList.remove(cls.state.active('x'));
      i.scrollbarXWidth = 0;
      i.scrollbarXLeft = 0;
      element.scrollLeft = i.isRtl === true ? i.contentWidth : 0;
    }
    if (i.scrollbarYActive) {
      element.classList.add(cls.state.active('y'));
    } else {
      element.classList.remove(cls.state.active('y'));
      i.scrollbarYHeight = 0;
      i.scrollbarYTop = 0;
      element.scrollTop = 0;
    }
  }

  function getThumbSize(i, thumbSize) {
    if (i.settings.minScrollbarLength) {
      thumbSize = Math.max(thumbSize, i.settings.minScrollbarLength);
    }
    if (i.settings.maxScrollbarLength) {
      thumbSize = Math.min(thumbSize, i.settings.maxScrollbarLength);
    }
    return thumbSize;
  }

  function updateCss(element, i) {
    var xRailOffset = { width: i.railXWidth };
    var roundedScrollTop = Math.floor(element.scrollTop);

    if (i.isRtl) {
      xRailOffset.left =
        i.negativeScrollAdjustment +
        element.scrollLeft +
        i.containerWidth -
        i.contentWidth;
    } else {
      xRailOffset.left = element.scrollLeft;
    }
    if (i.isScrollbarXUsingBottom) {
      xRailOffset.bottom = i.scrollbarXBottom - roundedScrollTop;
    } else {
      xRailOffset.top = i.scrollbarXTop + roundedScrollTop;
    }
    set(i.scrollbarXRail, xRailOffset);

    var yRailOffset = { top: roundedScrollTop, height: i.railYHeight };
    if (i.isScrollbarYUsingRight) {
      if (i.isRtl) {
        yRailOffset.right =
          i.contentWidth -
          (i.negativeScrollAdjustment + element.scrollLeft) -
          i.scrollbarYRight -
          i.scrollbarYOuterWidth -
          9;
      } else {
        yRailOffset.right = i.scrollbarYRight - element.scrollLeft;
      }
    } else {
      if (i.isRtl) {
        yRailOffset.left =
          i.negativeScrollAdjustment +
          element.scrollLeft +
          i.containerWidth * 2 -
          i.contentWidth -
          i.scrollbarYLeft -
          i.scrollbarYOuterWidth;
      } else {
        yRailOffset.left = i.scrollbarYLeft + element.scrollLeft;
      }
    }
    set(i.scrollbarYRail, yRailOffset);

    set(i.scrollbarX, {
      left: i.scrollbarXLeft,
      width: i.scrollbarXWidth - i.railBorderXWidth,
    });
    set(i.scrollbarY, {
      top: i.scrollbarYTop,
      height: i.scrollbarYHeight - i.railBorderYWidth,
    });
  }

  function clickRail(i) {
    var element = i.element;

    i.event.bind(i.scrollbarY, 'mousedown', function (e) { return e.stopPropagation(); });
    i.event.bind(i.scrollbarYRail, 'mousedown', function (e) {
      var positionTop =
        e.pageY -
        window.pageYOffset -
        i.scrollbarYRail.getBoundingClientRect().top;
      var direction = positionTop > i.scrollbarYTop ? 1 : -1;

      i.element.scrollTop += direction * i.containerHeight;
      updateGeometry(i);

      e.stopPropagation();
    });

    i.event.bind(i.scrollbarX, 'mousedown', function (e) { return e.stopPropagation(); });
    i.event.bind(i.scrollbarXRail, 'mousedown', function (e) {
      var positionLeft =
        e.pageX -
        window.pageXOffset -
        i.scrollbarXRail.getBoundingClientRect().left;
      var direction = positionLeft > i.scrollbarXLeft ? 1 : -1;

      i.element.scrollLeft += direction * i.containerWidth;
      updateGeometry(i);

      e.stopPropagation();
    });
  }

  function dragThumb(i) {
    bindMouseScrollHandler(i, [
      'containerWidth',
      'contentWidth',
      'pageX',
      'railXWidth',
      'scrollbarX',
      'scrollbarXWidth',
      'scrollLeft',
      'x',
      'scrollbarXRail' ]);
    bindMouseScrollHandler(i, [
      'containerHeight',
      'contentHeight',
      'pageY',
      'railYHeight',
      'scrollbarY',
      'scrollbarYHeight',
      'scrollTop',
      'y',
      'scrollbarYRail' ]);
  }

  function bindMouseScrollHandler(
    i,
    ref
  ) {
    var containerHeight = ref[0];
    var contentHeight = ref[1];
    var pageY = ref[2];
    var railYHeight = ref[3];
    var scrollbarY = ref[4];
    var scrollbarYHeight = ref[5];
    var scrollTop = ref[6];
    var y = ref[7];
    var scrollbarYRail = ref[8];

    var element = i.element;

    var startingScrollTop = null;
    var startingMousePageY = null;
    var scrollBy = null;

    function mouseMoveHandler(e) {
      if (e.touches && e.touches[0]) {
        e[pageY] = e.touches[0].pageY;
      }
      element[scrollTop] =
        startingScrollTop + scrollBy * (e[pageY] - startingMousePageY);
      addScrollingClass(i, y);
      updateGeometry(i);

      e.stopPropagation();
      e.preventDefault();
    }

    function mouseUpHandler() {
      removeScrollingClass(i, y);
      i[scrollbarYRail].classList.remove(cls.state.clicking);
      i.event.unbind(i.ownerDocument, 'mousemove', mouseMoveHandler);
    }

    function bindMoves(e, touchMode) {
      startingScrollTop = element[scrollTop];
      if (touchMode && e.touches) {
        e[pageY] = e.touches[0].pageY;
      }
      startingMousePageY = e[pageY];
      scrollBy =
        (i[contentHeight] - i[containerHeight]) /
        (i[railYHeight] - i[scrollbarYHeight]);
      if (!touchMode) {
        i.event.bind(i.ownerDocument, 'mousemove', mouseMoveHandler);
        i.event.once(i.ownerDocument, 'mouseup', mouseUpHandler);
        e.preventDefault();
      } else {
        i.event.bind(i.ownerDocument, 'touchmove', mouseMoveHandler);
      }

      i[scrollbarYRail].classList.add(cls.state.clicking);

      e.stopPropagation();
    }

    i.event.bind(i[scrollbarY], 'mousedown', function (e) {
      bindMoves(e);
    });
    i.event.bind(i[scrollbarY], 'touchstart', function (e) {
      bindMoves(e, true);
    });
  }

  function keyboard(i) {
    var element = i.element;

    var elementHovered = function () { return matches$1(element, ':hover'); };
    var scrollbarFocused = function () { return matches$1(i.scrollbarX, ':focus') || matches$1(i.scrollbarY, ':focus'); };

    function shouldPreventDefault(deltaX, deltaY) {
      var scrollTop = Math.floor(element.scrollTop);
      if (deltaX === 0) {
        if (!i.scrollbarYActive) {
          return false;
        }
        if (
          (scrollTop === 0 && deltaY > 0) ||
          (scrollTop >= i.contentHeight - i.containerHeight && deltaY < 0)
        ) {
          return !i.settings.wheelPropagation;
        }
      }

      var scrollLeft = element.scrollLeft;
      if (deltaY === 0) {
        if (!i.scrollbarXActive) {
          return false;
        }
        if (
          (scrollLeft === 0 && deltaX < 0) ||
          (scrollLeft >= i.contentWidth - i.containerWidth && deltaX > 0)
        ) {
          return !i.settings.wheelPropagation;
        }
      }
      return true;
    }

    i.event.bind(i.ownerDocument, 'keydown', function (e) {
      if (
        (e.isDefaultPrevented && e.isDefaultPrevented()) ||
        e.defaultPrevented
      ) {
        return;
      }

      if (!elementHovered() && !scrollbarFocused()) {
        return;
      }

      var activeElement = document.activeElement
        ? document.activeElement
        : i.ownerDocument.activeElement;
      if (activeElement) {
        if (activeElement.tagName === 'IFRAME') {
          activeElement = activeElement.contentDocument.activeElement;
        } else {
          // go deeper if element is a webcomponent
          while (activeElement.shadowRoot) {
            activeElement = activeElement.shadowRoot.activeElement;
          }
        }
        if (isEditable(activeElement)) {
          return;
        }
      }

      var deltaX = 0;
      var deltaY = 0;

      switch (e.which) {
        case 37: // left
          if (e.metaKey) {
            deltaX = -i.contentWidth;
          } else if (e.altKey) {
            deltaX = -i.containerWidth;
          } else {
            deltaX = -30;
          }
          break;
        case 38: // up
          if (e.metaKey) {
            deltaY = i.contentHeight;
          } else if (e.altKey) {
            deltaY = i.containerHeight;
          } else {
            deltaY = 30;
          }
          break;
        case 39: // right
          if (e.metaKey) {
            deltaX = i.contentWidth;
          } else if (e.altKey) {
            deltaX = i.containerWidth;
          } else {
            deltaX = 30;
          }
          break;
        case 40: // down
          if (e.metaKey) {
            deltaY = -i.contentHeight;
          } else if (e.altKey) {
            deltaY = -i.containerHeight;
          } else {
            deltaY = -30;
          }
          break;
        case 32: // space bar
          if (e.shiftKey) {
            deltaY = i.containerHeight;
          } else {
            deltaY = -i.containerHeight;
          }
          break;
        case 33: // page up
          deltaY = i.containerHeight;
          break;
        case 34: // page down
          deltaY = -i.containerHeight;
          break;
        case 36: // home
          deltaY = i.contentHeight;
          break;
        case 35: // end
          deltaY = -i.contentHeight;
          break;
        default:
          return;
      }

      if (i.settings.suppressScrollX && deltaX !== 0) {
        return;
      }
      if (i.settings.suppressScrollY && deltaY !== 0) {
        return;
      }

      element.scrollTop -= deltaY;
      element.scrollLeft += deltaX;
      updateGeometry(i);

      if (shouldPreventDefault(deltaX, deltaY)) {
        e.preventDefault();
      }
    });
  }

  function wheel(i) {
    var element = i.element;

    function shouldPreventDefault(deltaX, deltaY) {
      var roundedScrollTop = Math.floor(element.scrollTop);
      var isTop = element.scrollTop === 0;
      var isBottom =
        roundedScrollTop + element.offsetHeight === element.scrollHeight;
      var isLeft = element.scrollLeft === 0;
      var isRight =
        element.scrollLeft + element.offsetWidth === element.scrollWidth;

      var hitsBound;

      // pick axis with primary direction
      if (Math.abs(deltaY) > Math.abs(deltaX)) {
        hitsBound = isTop || isBottom;
      } else {
        hitsBound = isLeft || isRight;
      }

      return hitsBound ? !i.settings.wheelPropagation : true;
    }

    function getDeltaFromEvent(e) {
      var deltaX = e.deltaX;
      var deltaY = -1 * e.deltaY;

      if (typeof deltaX === 'undefined' || typeof deltaY === 'undefined') {
        // OS X Safari
        deltaX = (-1 * e.wheelDeltaX) / 6;
        deltaY = e.wheelDeltaY / 6;
      }

      if (e.deltaMode && e.deltaMode === 1) {
        // Firefox in deltaMode 1: Line scrolling
        deltaX *= 10;
        deltaY *= 10;
      }

      if (deltaX !== deltaX && deltaY !== deltaY /* NaN checks */) {
        // IE in some mouse drivers
        deltaX = 0;
        deltaY = e.wheelDelta;
      }

      if (e.shiftKey) {
        // reverse axis with shift key
        return [-deltaY, -deltaX];
      }
      return [deltaX, deltaY];
    }

    function shouldBeConsumedByChild(target, deltaX, deltaY) {
      // FIXME: this is a workaround for <select> issue in FF and IE #571
      if (!env.isWebKit && element.querySelector('select:focus')) {
        return true;
      }

      if (!element.contains(target)) {
        return false;
      }

      var cursor = target;

      while (cursor && cursor !== element) {
        if (cursor.classList.contains(cls.element.consuming)) {
          return true;
        }

        var style = get(cursor);

        // if deltaY && vertical scrollable
        if (deltaY && style.overflowY.match(/(scroll|auto)/)) {
          var maxScrollTop = cursor.scrollHeight - cursor.clientHeight;
          if (maxScrollTop > 0) {
            if (
              (cursor.scrollTop > 0 && deltaY < 0) ||
              (cursor.scrollTop < maxScrollTop && deltaY > 0)
            ) {
              return true;
            }
          }
        }
        // if deltaX && horizontal scrollable
        if (deltaX && style.overflowX.match(/(scroll|auto)/)) {
          var maxScrollLeft = cursor.scrollWidth - cursor.clientWidth;
          if (maxScrollLeft > 0) {
            if (
              (cursor.scrollLeft > 0 && deltaX < 0) ||
              (cursor.scrollLeft < maxScrollLeft && deltaX > 0)
            ) {
              return true;
            }
          }
        }

        cursor = cursor.parentNode;
      }

      return false;
    }

    function mousewheelHandler(e) {
      var ref = getDeltaFromEvent(e);
      var deltaX = ref[0];
      var deltaY = ref[1];

      if (shouldBeConsumedByChild(e.target, deltaX, deltaY)) {
        return;
      }

      var shouldPrevent = false;
      if (!i.settings.useBothWheelAxes) {
        // deltaX will only be used for horizontal scrolling and deltaY will
        // only be used for vertical scrolling - this is the default
        element.scrollTop -= deltaY * i.settings.wheelSpeed;
        element.scrollLeft += deltaX * i.settings.wheelSpeed;
      } else if (i.scrollbarYActive && !i.scrollbarXActive) {
        // only vertical scrollbar is active and useBothWheelAxes option is
        // active, so let's scroll vertical bar using both mouse wheel axes
        if (deltaY) {
          element.scrollTop -= deltaY * i.settings.wheelSpeed;
        } else {
          element.scrollTop += deltaX * i.settings.wheelSpeed;
        }
        shouldPrevent = true;
      } else if (i.scrollbarXActive && !i.scrollbarYActive) {
        // useBothWheelAxes and only horizontal bar is active, so use both
        // wheel axes for horizontal bar
        if (deltaX) {
          element.scrollLeft += deltaX * i.settings.wheelSpeed;
        } else {
          element.scrollLeft -= deltaY * i.settings.wheelSpeed;
        }
        shouldPrevent = true;
      }

      updateGeometry(i);

      shouldPrevent = shouldPrevent || shouldPreventDefault(deltaX, deltaY);
      if (shouldPrevent && !e.ctrlKey) {
        e.stopPropagation();
        e.preventDefault();
      }
    }

    if (typeof window.onwheel !== 'undefined') {
      i.event.bind(element, 'wheel', mousewheelHandler);
    } else if (typeof window.onmousewheel !== 'undefined') {
      i.event.bind(element, 'mousewheel', mousewheelHandler);
    }
  }

  function touch(i) {
    if (!env.supportsTouch && !env.supportsIePointer) {
      return;
    }

    var element = i.element;

    function shouldPrevent(deltaX, deltaY) {
      var scrollTop = Math.floor(element.scrollTop);
      var scrollLeft = element.scrollLeft;
      var magnitudeX = Math.abs(deltaX);
      var magnitudeY = Math.abs(deltaY);

      if (magnitudeY > magnitudeX) {
        // user is perhaps trying to swipe up/down the page

        if (
          (deltaY < 0 && scrollTop === i.contentHeight - i.containerHeight) ||
          (deltaY > 0 && scrollTop === 0)
        ) {
          // set prevent for mobile Chrome refresh
          return window.scrollY === 0 && deltaY > 0 && env.isChrome;
        }
      } else if (magnitudeX > magnitudeY) {
        // user is perhaps trying to swipe left/right across the page

        if (
          (deltaX < 0 && scrollLeft === i.contentWidth - i.containerWidth) ||
          (deltaX > 0 && scrollLeft === 0)
        ) {
          return true;
        }
      }

      return true;
    }

    function applyTouchMove(differenceX, differenceY) {
      element.scrollTop -= differenceY;
      element.scrollLeft -= differenceX;

      updateGeometry(i);
    }

    var startOffset = {};
    var startTime = 0;
    var speed = {};
    var easingLoop = null;

    function getTouch(e) {
      if (e.targetTouches) {
        return e.targetTouches[0];
      } else {
        // Maybe IE pointer
        return e;
      }
    }

    function shouldHandle(e) {
      if (e.pointerType && e.pointerType === 'pen' && e.buttons === 0) {
        return false;
      }
      if (e.targetTouches && e.targetTouches.length === 1) {
        return true;
      }
      if (
        e.pointerType &&
        e.pointerType !== 'mouse' &&
        e.pointerType !== e.MSPOINTER_TYPE_MOUSE
      ) {
        return true;
      }
      return false;
    }

    function touchStart(e) {
      if (!shouldHandle(e)) {
        return;
      }

      var touch = getTouch(e);

      startOffset.pageX = touch.pageX;
      startOffset.pageY = touch.pageY;

      startTime = new Date().getTime();

      if (easingLoop !== null) {
        clearInterval(easingLoop);
      }
    }

    function shouldBeConsumedByChild(target, deltaX, deltaY) {
      if (!element.contains(target)) {
        return false;
      }

      var cursor = target;

      while (cursor && cursor !== element) {
        if (cursor.classList.contains(cls.element.consuming)) {
          return true;
        }

        var style = get(cursor);

        // if deltaY && vertical scrollable
        if (deltaY && style.overflowY.match(/(scroll|auto)/)) {
          var maxScrollTop = cursor.scrollHeight - cursor.clientHeight;
          if (maxScrollTop > 0) {
            if (
              (cursor.scrollTop > 0 && deltaY < 0) ||
              (cursor.scrollTop < maxScrollTop && deltaY > 0)
            ) {
              return true;
            }
          }
        }
        // if deltaX && horizontal scrollable
        if (deltaX && style.overflowX.match(/(scroll|auto)/)) {
          var maxScrollLeft = cursor.scrollWidth - cursor.clientWidth;
          if (maxScrollLeft > 0) {
            if (
              (cursor.scrollLeft > 0 && deltaX < 0) ||
              (cursor.scrollLeft < maxScrollLeft && deltaX > 0)
            ) {
              return true;
            }
          }
        }

        cursor = cursor.parentNode;
      }

      return false;
    }

    function touchMove(e) {
      if (shouldHandle(e)) {
        var touch = getTouch(e);

        var currentOffset = { pageX: touch.pageX, pageY: touch.pageY };

        var differenceX = currentOffset.pageX - startOffset.pageX;
        var differenceY = currentOffset.pageY - startOffset.pageY;

        if (shouldBeConsumedByChild(e.target, differenceX, differenceY)) {
          return;
        }

        applyTouchMove(differenceX, differenceY);
        startOffset = currentOffset;

        var currentTime = new Date().getTime();

        var timeGap = currentTime - startTime;
        if (timeGap > 0) {
          speed.x = differenceX / timeGap;
          speed.y = differenceY / timeGap;
          startTime = currentTime;
        }

        if (shouldPrevent(differenceX, differenceY)) {
          e.preventDefault();
        }
      }
    }
    function touchEnd() {
      if (i.settings.swipeEasing) {
        clearInterval(easingLoop);
        easingLoop = setInterval(function() {
          if (i.isInitialized) {
            clearInterval(easingLoop);
            return;
          }

          if (!speed.x && !speed.y) {
            clearInterval(easingLoop);
            return;
          }

          if (Math.abs(speed.x) < 0.01 && Math.abs(speed.y) < 0.01) {
            clearInterval(easingLoop);
            return;
          }

          applyTouchMove(speed.x * 30, speed.y * 30);

          speed.x *= 0.8;
          speed.y *= 0.8;
        }, 10);
      }
    }

    if (env.supportsTouch) {
      i.event.bind(element, 'touchstart', touchStart);
      i.event.bind(element, 'touchmove', touchMove);
      i.event.bind(element, 'touchend', touchEnd);
    } else if (env.supportsIePointer) {
      if (window.PointerEvent) {
        i.event.bind(element, 'pointerdown', touchStart);
        i.event.bind(element, 'pointermove', touchMove);
        i.event.bind(element, 'pointerup', touchEnd);
      } else if (window.MSPointerEvent) {
        i.event.bind(element, 'MSPointerDown', touchStart);
        i.event.bind(element, 'MSPointerMove', touchMove);
        i.event.bind(element, 'MSPointerUp', touchEnd);
      }
    }
  }

  var defaultSettings = function () { return ({
    handlers: ['click-rail', 'drag-thumb', 'keyboard', 'wheel', 'touch'],
    maxScrollbarLength: null,
    minScrollbarLength: null,
    scrollingThreshold: 1000,
    scrollXMarginOffset: 0,
    scrollYMarginOffset: 0,
    suppressScrollX: false,
    suppressScrollY: false,
    swipeEasing: true,
    useBothWheelAxes: false,
    wheelPropagation: true,
    wheelSpeed: 1,
  }); };

  var handlers = {
    'click-rail': clickRail,
    'drag-thumb': dragThumb,
    keyboard: keyboard,
    wheel: wheel,
    touch: touch,
  };

  var PerfectScrollbar = function PerfectScrollbar(element, userSettings) {
    var this$1 = this;
    if ( userSettings === void 0 ) userSettings = {};

    if (typeof element === 'string') {
      element = document.querySelector(element);
    }

    if (!element || !element.nodeName) {
      throw new Error('no element is specified to initialize PerfectScrollbar');
    }

    this.element = element;

    element.classList.add(cls.main);

    this.settings = defaultSettings();
    for (var key in userSettings) {
      this.settings[key] = userSettings[key];
    }

    this.containerWidth = null;
    this.containerHeight = null;
    this.contentWidth = null;
    this.contentHeight = null;

    var focus = function () { return element.classList.add(cls.state.focus); };
    var blur = function () { return element.classList.remove(cls.state.focus); };

    this.isRtl = get(element).direction === 'rtl';
    if (this.isRtl === true) {
      element.classList.add(cls.rtl);
    }
    this.isNegativeScroll = (function () {
      var originalScrollLeft = element.scrollLeft;
      var result = null;
      element.scrollLeft = -1;
      result = element.scrollLeft < 0;
      element.scrollLeft = originalScrollLeft;
      return result;
    })();
    this.negativeScrollAdjustment = this.isNegativeScroll
      ? element.scrollWidth - element.clientWidth
      : 0;
    this.event = new EventManager();
    this.ownerDocument = element.ownerDocument || document;

    this.scrollbarXRail = div$1(cls.element.rail('x'));
    element.appendChild(this.scrollbarXRail);
    this.scrollbarX = div$1(cls.element.thumb('x'));
    this.scrollbarXRail.appendChild(this.scrollbarX);
    this.scrollbarX.setAttribute('tabindex', 0);
    this.event.bind(this.scrollbarX, 'focus', focus);
    this.event.bind(this.scrollbarX, 'blur', blur);
    this.scrollbarXActive = null;
    this.scrollbarXWidth = null;
    this.scrollbarXLeft = null;
    var railXStyle = get(this.scrollbarXRail);
    this.scrollbarXBottom = parseInt(railXStyle.bottom, 10);
    if (isNaN(this.scrollbarXBottom)) {
      this.isScrollbarXUsingBottom = false;
      this.scrollbarXTop = toInt(railXStyle.top);
    } else {
      this.isScrollbarXUsingBottom = true;
    }
    this.railBorderXWidth =
      toInt(railXStyle.borderLeftWidth) + toInt(railXStyle.borderRightWidth);
    // Set rail to display:block to calculate margins
    set(this.scrollbarXRail, { display: 'block' });
    this.railXMarginWidth =
      toInt(railXStyle.marginLeft) + toInt(railXStyle.marginRight);
    set(this.scrollbarXRail, { display: '' });
    this.railXWidth = null;
    this.railXRatio = null;

    this.scrollbarYRail = div$1(cls.element.rail('y'));
    element.appendChild(this.scrollbarYRail);
    this.scrollbarY = div$1(cls.element.thumb('y'));
    this.scrollbarYRail.appendChild(this.scrollbarY);
    this.scrollbarY.setAttribute('tabindex', 0);
    this.event.bind(this.scrollbarY, 'focus', focus);
    this.event.bind(this.scrollbarY, 'blur', blur);
    this.scrollbarYActive = null;
    this.scrollbarYHeight = null;
    this.scrollbarYTop = null;
    var railYStyle = get(this.scrollbarYRail);
    this.scrollbarYRight = parseInt(railYStyle.right, 10);
    if (isNaN(this.scrollbarYRight)) {
      this.isScrollbarYUsingRight = false;
      this.scrollbarYLeft = toInt(railYStyle.left);
    } else {
      this.isScrollbarYUsingRight = true;
    }
    this.scrollbarYOuterWidth = this.isRtl ? outerWidth(this.scrollbarY) : null;
    this.railBorderYWidth =
      toInt(railYStyle.borderTopWidth) + toInt(railYStyle.borderBottomWidth);
    set(this.scrollbarYRail, { display: 'block' });
    this.railYMarginHeight =
      toInt(railYStyle.marginTop) + toInt(railYStyle.marginBottom);
    set(this.scrollbarYRail, { display: '' });
    this.railYHeight = null;
    this.railYRatio = null;

    this.reach = {
      x:
        element.scrollLeft <= 0
          ? 'start'
          : element.scrollLeft >= this.contentWidth - this.containerWidth
          ? 'end'
          : null,
      y:
        element.scrollTop <= 0
          ? 'start'
          : element.scrollTop >= this.contentHeight - this.containerHeight
          ? 'end'
          : null,
    };

    this.isAlive = true;

    this.settings.handlers.forEach(function (handlerName) { return handlers[handlerName](this$1); });

    this.lastScrollTop = Math.floor(element.scrollTop); // for onScroll only
    this.lastScrollLeft = element.scrollLeft; // for onScroll only
    this.event.bind(this.element, 'scroll', function (e) { return this$1.onScroll(e); });
    updateGeometry(this);
  };

  PerfectScrollbar.prototype.update = function update () {
    if (!this.isAlive) {
      return;
    }

    // Recalcuate negative scrollLeft adjustment
    this.negativeScrollAdjustment = this.isNegativeScroll
      ? this.element.scrollWidth - this.element.clientWidth
      : 0;

    // Recalculate rail margins
    set(this.scrollbarXRail, { display: 'block' });
    set(this.scrollbarYRail, { display: 'block' });
    this.railXMarginWidth =
      toInt(get(this.scrollbarXRail).marginLeft) +
      toInt(get(this.scrollbarXRail).marginRight);
    this.railYMarginHeight =
      toInt(get(this.scrollbarYRail).marginTop) +
      toInt(get(this.scrollbarYRail).marginBottom);

    // Hide scrollbars not to affect scrollWidth and scrollHeight
    set(this.scrollbarXRail, { display: 'none' });
    set(this.scrollbarYRail, { display: 'none' });

    updateGeometry(this);

    processScrollDiff(this, 'top', 0, false, true);
    processScrollDiff(this, 'left', 0, false, true);

    set(this.scrollbarXRail, { display: '' });
    set(this.scrollbarYRail, { display: '' });
  };

  PerfectScrollbar.prototype.onScroll = function onScroll (e) {
    if (!this.isAlive) {
      return;
    }

    updateGeometry(this);
    processScrollDiff(this, 'top', this.element.scrollTop - this.lastScrollTop);
    processScrollDiff(
      this,
      'left',
      this.element.scrollLeft - this.lastScrollLeft
    );

    this.lastScrollTop = Math.floor(this.element.scrollTop);
    this.lastScrollLeft = this.element.scrollLeft;
  };

  PerfectScrollbar.prototype.destroy = function destroy () {
    if (!this.isAlive) {
      return;
    }

    this.event.unbindAll();
    remove(this.scrollbarX);
    remove(this.scrollbarY);
    remove(this.scrollbarXRail);
    remove(this.scrollbarYRail);
    this.removePsClasses();

    // unset elements
    this.element = null;
    this.scrollbarX = null;
    this.scrollbarY = null;
    this.scrollbarXRail = null;
    this.scrollbarYRail = null;

    this.isAlive = false;
  };

  PerfectScrollbar.prototype.removePsClasses = function removePsClasses () {
    this.element.className = this.element.className
      .split(' ')
      .filter(function (name) { return !name.match(/^ps([-_].+|)$/); })
      .join(' ');
  };

  /* eslint-env browser */
  class VPerfectScroll extends HTMLElement {
    connectedCallback() {
      this.scroll = new PerfectScrollbar(this.parentElement);
    }

    disconnectedCallback() {
      this.scroll.destroy();
    }

  }

  function _defineProperty$2(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
  class VSnackbar extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$2(this, "onShowSnackbarEvent", event => {
        this._showSnackBar(event.detail.message, event.detail.actionText, event.detail.actionLink);
      });
    }

    connectedCallback() {
      setTimeout(() => {
        window.addEventListener('vf-snackbar:show', this.onShowSnackbarEvent, false);

        this._showInitialSnackbar();
      });
    }

    disconnectedCallback() {
      if (this._mdcSnackbar) {
        this._mdcSnackbar.destroy();
      }

      window.removeEventListener('vf-snackbar:show', this.onShowSnackbarEvent);
    }

    _showSnackBar(message, actionText, actionLink) {
      const surface = div({
        class: 'mdc-snackbar__surface'
      }).with([div({
        class: 'mdc-snackbar__label'
      }).text(message), actionText ? div({
        class: 'mdc-snackbar__actions'
      }).with([a({
        class: 'mdc-button mdc-snackbar__action',
        href: actionLink
      }).text(actionText)]) : null]);

      if (this._mdcSnackbar) {
        this._mdcSnackbar.destroy();
      }

      this.innerHTML = surface.toDOM().outerHTML;
      this._mdcSnackbar = materialComponentsWeb.snackbar.MDCSnackbar.attachTo(this);

      this._mdcSnackbar.open();
    }

    _showInitialSnackbar() {
      let actionText; // let actionHandler;

      const message = Array.prototype.filter.call(this.childNodes, child => {
        return child.nodeType === Node.TEXT_NODE;
      }).map(child => {
        return child.textContent.trim();
      }).join(' ');
      const link = this.querySelector('a');

      if (link && window.location.href !== link.href) {
        actionText = link.textContent; // actionHandler = () => {
        //   if (Turbolinks) {
        //     Turbolinks.visit(link.href);
        //   } else {
        //     window.location = link.href;
        //   }
        // };
      }

      if (message) {
        this._showSnackBar(message, actionText, link ? link.href : null);
      }
    }

  }

  function _defineProperty$3(obj, key, value) { if (key in obj) { Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true }); } else { obj[key] = value; } return obj; }
  class VTurbolinks extends HTMLElement {
    constructor(...args) {
      super(...args);

      _defineProperty$3(this, "onRequestEnd", event => {
        if (event.data.xhr.status >= 400) {
          Turbolinks__default['default'].controller.disable();
        }
      });
    }

    connectedCallback() {
      document.addEventListener('turbolinks:request-end', this.onRequestEnd);
    }

    disconnectedCallback() {
      document.removeEventListener('turbolinks:request-end', this.onRequestEnd);
    }

  }

  /* eslint-env browser */
  window.addEventListener('DOMContentLoaded', () => {
    window.customElements.define('vf-card-menu', VCardMenu);
    window.customElements.define('vf-page-menu-navigation', VPageMenuNavigation);
    window.customElements.define('vf-page-menu-toggle', VPageMenuToggle);
    window.customElements.define('vf-page-scroll-fix', VPageScrollFix);
    window.customElements.define('vf-page', VPage);
    window.customElements.define('vf-perfect-scroll', VPerfectScroll);
    window.customElements.define('vf-snackbar', VSnackbar);
    window.customElements.define('vf-turbolinks', VTurbolinks);
  });

}(Turbolinks, mdc));
//# sourceMappingURL=viewflow-components.js.map
