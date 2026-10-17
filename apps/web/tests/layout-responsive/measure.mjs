/**
 * Pure geometry evaluator and browser DOM measurement script for SPEC-002 (P01, P02, P03).
 * No external dependencies.
 */

export const DASHBOARD_ROUTES = ["/", "/retos", "/mesociclos", "/70-3-cartagena"];
export const CHAT_SYNTHETIC_ROUTE = "/chat?conversation=layout-synthetic";

export const MATRIX_S_CELLS = [
  { route: "/", width: 375, height: 812, kind: "dashboard" },
  { route: "/", width: 800, height: 812, kind: "dashboard" },
  { route: "/", width: 801, height: 900, kind: "dashboard" },
  { route: "/", width: 1600, height: 900, kind: "dashboard" },
  { route: "/retos", width: 375, height: 812, kind: "dashboard" },
  { route: "/retos", width: 1600, height: 900, kind: "dashboard" },
  { route: "/mesociclos", width: 375, height: 812, kind: "dashboard" },
  { route: "/mesociclos", width: 1600, height: 900, kind: "dashboard" },
  { route: "/70-3-cartagena", width: 375, height: 812, kind: "dashboard" },
  { route: "/70-3-cartagena", width: 1600, height: 900, kind: "dashboard" },
  { route: CHAT_SYNTHETIC_ROUTE, width: 375, height: 812, kind: "chat" },
  { route: CHAT_SYNTHETIC_ROUTE, width: 800, height: 812, kind: "chat" },
  { route: CHAT_SYNTHETIC_ROUTE, width: 801, height: 900, kind: "chat" },
  { route: CHAT_SYNTHETIC_ROUTE, width: 1600, height: 900, kind: "chat" },
];

export function computeExpectedDashboardGeometry(viewportWidth, appMainWidth) {
  const isMobile = viewportWidth <= 800;
  const expectedW = isMobile ? appMainWidth : Math.min(appMainWidth, 1120);
  const expectedPadding = isMobile ? 16 : 28;
  const expectedMargin = (appMainWidth - expectedW) / 2;
  const expectedContentWidth = expectedW - 2 * expectedPadding;
  return {
    isMobile,
    expectedW,
    expectedPadding,
    expectedMargin,
    expectedContentWidth,
  };
}

export function evaluateCellMeasurement(cell) {
  const errors = [];

  if (cell.globalOverflow > 1) {
    errors.push(`Global horizontal overflow ${cell.globalOverflow}px exceeds 1px limit`);
  }

  if (Array.isArray(cell.controlsOutOfBounds) && cell.controlsOutOfBounds.length > 0) {
    errors.push(`Controls out of bounds: ${cell.controlsOutOfBounds.join(", ")}`);
  }

  if (cell.kind === "dashboard") {
    const exp = computeExpectedDashboardGeometry(cell.clientWidth, cell.appMainWidth);
    if (Math.abs(cell.mainWidth - exp.expectedW) > 2) {
      errors.push(`mainWidth ${cell.mainWidth} deviates >2px from expected ${exp.expectedW}`);
    }
    if (Math.abs(cell.paddingLeft - exp.expectedPadding) > 2) {
      errors.push(`paddingLeft ${cell.paddingLeft} deviates >2px from expected ${exp.expectedPadding}`);
    }
    if (Math.abs(cell.paddingRight - exp.expectedPadding) > 2) {
      errors.push(`paddingRight ${cell.paddingRight} deviates >2px from expected ${exp.expectedPadding}`);
    }
    if (Math.abs(cell.marginLeft - cell.marginRight) > 2) {
      errors.push(
        `margin asymmetry |${cell.marginLeft} - ${cell.marginRight}| = ${Math.abs(cell.marginLeft - cell.marginRight)}px exceeds 2px`
      );
    }
    if (Math.abs(cell.marginLeft - exp.expectedMargin) > 2) {
      errors.push(`marginLeft ${cell.marginLeft} deviates >2px from expected ${exp.expectedMargin}`);
    }
    if (cell.internalScroll && cell.internalScroll.scrollWidth > cell.internalScroll.clientWidth + 1) {
      if (!cell.internalScroll.canReachEnd) {
        errors.push("Internal scroll container could not reach its horizontal end");
      }
      if (Math.abs(cell.internalScroll.docScrollLeftAfter) > 1) {
        errors.push(`Document scrolled horizontally (${cell.internalScroll.docScrollLeftAfter}px) during internal scroll`);
      }
    }
  } else if (cell.kind === "chat") {
    if (Math.abs(cell.chatMainWidth - cell.clientWidth) > 2) {
      errors.push(`chatMainWidth ${cell.chatMainWidth} deviates >2px from clientWidth ${cell.clientWidth}`);
    }
    if (cell.composerWidth > 880 + 2) {
      errors.push(`composerWidth ${cell.composerWidth} exceeds 880px + 2px tolerance`);
    }
    if (Math.abs(cell.composerMarginLeft - cell.composerMarginRight) > 2) {
      errors.push(
        `composer margin asymmetry |${cell.composerMarginLeft} - ${cell.composerMarginRight}| exceeds 2px`
      );
    }
    if (cell.userAlignSelf && cell.userAlignSelf !== "flex-end") {
      errors.push(`Expected user bubble align-self flex-end, got ${cell.userAlignSelf}`);
    }
    if (cell.assistantAlignSelf && cell.assistantAlignSelf !== "flex-start") {
      errors.push(`Expected assistant bubble align-self flex-start, got ${cell.assistantAlignSelf}`);
    }
  }

  return {
    pass: errors.length === 0,
    errors,
  };
}

export const BROWSER_MEASURE_SCRIPT = `(function() {
  const docEl = document.documentElement;
  const body = document.body;
  const clientWidth = docEl.clientWidth;
  const innerWidth = window.innerWidth;
  const scrollWidth = Math.max(body ? body.scrollWidth : 0, docEl.scrollWidth);
  const globalOverflow = scrollWidth - clientWidth;
  const pathname = window.location.pathname;
  const search = window.location.search;
  const route = pathname + search;
  const isChat = pathname.startsWith('/chat');

  const controlsOutOfBounds = [];
  const selectors = isChat
    ? ['.chat-back', '.chat-header-btn', '#chat-screen-input', '.coach-model-select select', '.coach-send']
    : ['.dash-refresh', '.dash-nav-link', '#coach-dashboard-input', '.coach-send', '.coach-new'];

  for (const sel of selectors) {
    const nodes = Array.from(document.querySelectorAll(sel));
    for (const el of nodes) {
      const style = window.getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      if (el.closest('.dash-nav-scroll-area')) {
        el.scrollIntoView({ inline: 'nearest', block: 'nearest' });
      }
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) {
        controlsOutOfBounds.push(sel + ':zero-size');
      } else if (r.left < -1.5 || r.right > clientWidth + 1.5) {
        controlsOutOfBounds.push(sel + ':out-of-viewport(' + Math.round(r.left) + ',' + Math.round(r.right) + ')');
      }
    }
  }
  const navScroll = document.querySelector('.dash-nav-scroll-area');
  if (navScroll) navScroll.scrollLeft = 0;

  if (!isChat) {
    const appMain = document.querySelector('.app-main');
    const main = document.querySelector('.app-main > main') || document.querySelector('main');
    const appMainRect = appMain ? appMain.getBoundingClientRect() : { left: 0, right: clientWidth, width: clientWidth };
    const mainRect = main ? main.getBoundingClientRect() : { left: 0, right: 0, width: 0 };
    const mainStyle = main ? window.getComputedStyle(main) : { paddingLeft: '0', paddingRight: '0' };
    const paddingLeft = parseFloat(mainStyle.paddingLeft) || 0;
    const paddingRight = parseFloat(mainStyle.paddingRight) || 0;
    const marginLeft = mainRect.left - appMainRect.left;
    const marginRight = appMainRect.right - mainRect.right;

    let internalScroll = null;
    const prepWrap = document.querySelector('.prep-chart-wrap');
    if (prepWrap) {
      const before = prepWrap.scrollLeft;
      const maxScroll = prepWrap.scrollWidth - prepWrap.clientWidth;
      if (maxScroll > 1) {
        prepWrap.scrollLeft = maxScroll;
      }
      const reached = prepWrap.scrollLeft;
      const docScrollLeftAfter = window.scrollX || docEl.scrollLeft || 0;
      prepWrap.scrollLeft = before;
      internalScroll = {
        selector: '.prep-chart-wrap',
        scrollWidth: Math.round(prepWrap.scrollWidth),
        clientWidth: Math.round(prepWrap.clientWidth),
        maxScroll: Math.round(maxScroll),
        reachedScrollLeft: Math.round(reached),
        canReachEnd: maxScroll <= 1 || Math.abs(reached - maxScroll) <= 2,
        docScrollLeftAfter: Math.round(docScrollLeftAfter)
      };
    }

    return JSON.stringify({
      kind: 'dashboard',
      route,
      innerWidth,
      clientWidth,
      devicePixelRatio: window.devicePixelRatio,
      mediaMaxWidth800: window.matchMedia('(max-width: 800px)').matches,
      scrollWidth,
      globalOverflow,
      appMainWidth: Math.round(appMainRect.width * 100) / 100,
      mainWidth: Math.round(mainRect.width * 100) / 100,
      paddingLeft: Math.round(paddingLeft * 100) / 100,
      paddingRight: Math.round(paddingRight * 100) / 100,
      contentWidth: Math.round((mainRect.width - paddingLeft - paddingRight) * 100) / 100,
      marginLeft: Math.round(marginLeft * 100) / 100,
      marginRight: Math.round(marginRight * 100) / 100,
      marginDiff: Math.round(Math.abs(marginLeft - marginRight) * 100) / 100,
      controlsOutOfBounds,
      internalScroll,
      versionText: (document.querySelector('.dash-version')?.textContent || '').trim()
    });
  } else {
    const chatMain = document.querySelector('.chat-main');
    const composerWrap = document.querySelector('.chat-composer-wrap');
    const composer = document.querySelector('.chat-composer');
    const userRow = document.querySelector('.chat-row-user');
    const assistantRow = document.querySelector('.chat-row-assistant');
    const chatMainRect = chatMain ? chatMain.getBoundingClientRect() : { width: 0, left: 0, right: 0 };
    const wrapRect = composerWrap ? composerWrap.getBoundingClientRect() : { width: clientWidth, left: 0, right: clientWidth };
    const wrapStyle = composerWrap ? window.getComputedStyle(composerWrap) : { paddingLeft: '0', paddingRight: '0' };
    const wrapInnerLeft = wrapRect.left + (parseFloat(wrapStyle.paddingLeft) || 0);
    const wrapInnerRight = wrapRect.right - (parseFloat(wrapStyle.paddingRight) || 0);
    const composerRect = composer ? composer.getBoundingClientRect() : { width: 0, left: 0, right: 0 };
    const composerMarginLeft = composerRect.left - wrapInnerLeft;
    const composerMarginRight = wrapInnerRight - composerRect.right;

    return JSON.stringify({
      kind: 'chat',
      route,
      innerWidth,
      clientWidth,
      devicePixelRatio: window.devicePixelRatio,
      mediaMaxWidth800: window.matchMedia('(max-width: 800px)').matches,
      scrollWidth,
      globalOverflow,
      chatMainWidth: Math.round(chatMainRect.width * 100) / 100,
      composerWidth: Math.round(composerRect.width * 100) / 100,
      composerMarginLeft: Math.round(composerMarginLeft * 100) / 100,
      composerMarginRight: Math.round(composerMarginRight * 100) / 100,
      composerMarginDiff: Math.round(Math.abs(composerMarginLeft - composerMarginRight) * 100) / 100,
      userAlignSelf: userRow ? window.getComputedStyle(userRow).alignSelf : null,
      assistantAlignSelf: assistantRow ? window.getComputedStyle(assistantRow).alignSelf : null,
      controlsOutOfBounds
    });
  }
})()`;
