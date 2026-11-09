/**
 * CodeProOJ - Universal Bilingual Internationalization (i18n) Engine
 * Supported Languages:
 *   - vi: Tiếng Việt (Default)
 *   - en: English
 * Features:
 *   - Full recursive DOM Tree Walker with text node caching (no text left untranslated)
 *   - Automatic translation of Placeholders, Titles, Select Options, Buttons, Tables, Badges
 *   - MutationObserver to automatically translate dynamic content loaded via Fetch/AJAX APIs
 *   - Lossless 2-way switching (VI <-> EN)
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'cp_lang';
  const SUPPORTED_LANGS = ['vi', 'en'];

  // ══════════════════════════════════════════════════════════════════════
  // 1. EXTENSIVE BILINGUAL TRANSLATION PHRASES (SORTED BY LENGTH FOR GREEDY MATCH)
  // ══════════════════════════════════════════════════════════════════════
  const PHRASE_PAIRS = [
    ["Tải Client", "Download Client"],
    // Long Sentences & Paragraphs
    ["Hệ thống thi đấu trực tuyến và máy chấm bài tự động chuẩn quốc tế. Cung cấp kho đề thi phong phú từ HSG Tỉnh, HSG Quốc Gia, Olympic Tin học đến ICPC.", "International standard online competitive programming judge platform. Offering rich problem sets from Provincial & National Olympiads to ICPC."],
    ["Hệ thống bài giảng và code mẫu chuẩn C++ các thuật toán kinh điển trong lập trình thi đấu.", "Lectures and standard C++ code templates for classic algorithms in competitive programming."],
    ["Luyện tập thuật toán chuẩn Olympic Tin học và ICPC với hệ thống máy chấm CodeProOJ tự động.", "Practice Olympiad and ICPC algorithms with the automated CodeProOJ judge system."],
    ["Nền tảng thi đấu lập trình trực tuyến & cộng đồng Olympic Tin học Việt Nam.", "Online competitive programming platform & Vietnamese Informatics Olympiad community."],
    ["Thống kê thứ hạng thành viên dựa trên kỹ năng, điểm số và cấp bậc Elo/Codeforces.", "Member ranking statistics based on skill, points, and Elo rating tiers."],
    ["Luyện Tập Thuật Toán • Chinh Phục Olympic", "Algorithmic Practice • Conquer Olympiad"],
    ["Không thể tải dữ liệu bài nộp. Vui lòng thử lại sau.", "Failed to load submissions. Please try again later."],
    ["Đang tải dữ liệu bài tập từ máy chủ...", "Loading problem set from server..."],
    ["Đang tải thông tin hồ sơ...", "Loading profile data..."],
    ["Đang tải danh sách bài nộp...", "Loading submissions list..."],
    ["Đang tải bảng xếp hạng...", "Loading leaderboard..."],
    ["Chưa có bài nộp nào.", "No submissions yet."],
    ["Chưa có bài nộp nào", "No submissions yet"],
    ["Không tìm thấy bài nộp nào", "No submissions found"],
    ["Không tìm thấy người dùng", "User Not Found"],
    ["Xem lịch sử bài nộp của bạn", "View your submission history"],
    ["Tìm kiếm theo mã bài (SUMA, MAXSUM...), tên bài...", "Search by code (SUMA, MAXSUM...), title..."],
    ["Tìm kiếm thành viên hoặc trường...", "Search member or school..."],

    // Section Titles & Headers
    ["Bài tập tuyển chọn (Featured Problems)", "Featured Problems"],
    ["Bài tập tuyển chọn", "Featured Problems"],
    ["CodePro Wiki - Chuyên đề cốt lõi", "CodePro Wiki - Core Topics"],
    ["Tin tức & Thông báo mới nhất", "Latest News & Announcements"],
    ["Kỳ thi tâm điểm", "Spotlight Contest"],
    ["Bảng vàng Top Coders", "Top Coders Hall of Fame"],
    ["Bài nộp thời gian thực", "Real-Time Submissions"],
    ["Kho Bài Tập Lập Trình", "Programming Problem Set"],
    ["Kho Bài Tập Thuật Toán", "Algorithm Problem Set"],
    ["Kho Bài Tập", "Problem Set"],
    ["Bảng xếp hạng Lập trình thi đấu", "Competitive Programming Leaderboard"],
    ["Bảng xếp hạng Tổng thể", "Global Leaderboard"],
    ["Bảng Xếp Hạng Toàn Server", "Global Leaderboard"],
    ["Bảng xếp hạng toàn cầu", "Global Leaderboard"],
    ["Bảng Điểm Rating", "Rating Leaderboard"],
    ["Trạng thái & Lịch sử nộp bài", "Submission Status & History"],
    ["Thống kê giải bài (Statistics)", "Problem Solving Statistics"],
    ["Thống kê giải bài", "Problem Solving Statistics"],
    ["Phân bố kết quả bài nộp", "Submission Verdict Distribution"],
    ["Bài nộp gần đây (Recent Submissions)", "Recent Submissions"],
    ["Bài nộp gần đây", "Recent Submissions"],
    ["Lịch sử nộp bài", "Submission History"],
    ["Lịch sử rating", "Rating History"],
    ["BÀI NỘP CỦA BẠN", "YOUR SUBMISSIONS"],
    ["CHỦ ĐỀ & TÁC GIẢ", "TOPIC & AUTHOR"],
    ["Lời giải tốt nhất", "Best Solutions"],
    ["Đầu vào (Input)", "Input Format"],
    ["Đầu ra (Output)", "Output Format"],
    ["Ví dụ đầu vào", "Sample Input"],
    ["Ví dụ đầu ra", "Sample Output"],
    ["Giới hạn thời gian", "Time Limit"],
    ["Giới hạn bộ nhớ", "Memory Limit"],
    ["Thời gian chạy", "Execution Time"],
    ["Bộ nhớ sử dụng", "Memory Used"],
    ["Mã nguồn", "Source Code"],
    ["Xem mã nguồn", "View Source Code"],
    ["Tải mã nguồn", "Download Code"],
    ["Quay về Trang chủ", "Back to Home"],

    // Algorithms & Topics
    ["Quy hoạch động (DP)", "Dynamic Programming (DP)"],
    ["Cây phân đoạn (Segment Tree)", "Segment Tree"],
    ["Đường đi ngắn nhất", "Shortest Path"],
    ["Thư viện chuẩn C++ STL", "C++ STL Library"],
    ["Quy hoạch động", "Dynamic Programming"],
    ["Cấu trúc dữ liệu", "Data Structures"],
    ["Tìm kiếm nhị phân", "Binary Search"],
    ["Lý thuyết đồ thị", "Graph Theory"],
    ["Hình học tính toán", "Computational Geometry"],
    ["Số học & Đại số", "Number Theory & Algebra"],
    ["Xâu ký tự", "Strings"],
    ["Toán học", "Mathematics"],
    ["Cơ bản", "Fundamentals"],
    ["Đồ thị", "Graphs"],

    // Stats & Metrics
    ["Thành viên (Coders)", "Members (Coders)"],
    ["Bài bạn đã giải (AC)", "Problems You Solved (AC)"],
    ["Tỷ lệ AC trung bình", "Average AC Rate"],
    ["Tổng điểm tích lũy", "Total Points Earned"],
    ["Tổng số bài tập", "Total Problems"],
    ["Lượt nộp bài (Subs)", "Submissions"],
    ["Lượt nộp bài", "Submissions"],
    ["Kỳ thi tổ chức", "Contests Hosted"],
    ["Rating hiện tại", "Current Rating"],
    ["Điểm tích lũy", "Points Earned"],
    ["Tổng bài nộp", "Total Submissions"],
    ["Số bài đã giải", "Solved Problems"],
    ["Số bài đã nộp", "Total Submissions"],
    ["Kết quả cao nhất:", "Best Verdict:"],
    ["Thời điểm nộp", "Submitted At"],

    // Navigation & Actions
    ["Khám phá Kho Bài Tập", "Explore Problem Set"],
    ["Vào thư viện Wiki", "Open Wiki Library"],
    ["Tham gia Kỳ Thi", "Join Contests"],
    ["Thư viện CodePro Wiki", "CodePro Wiki Library"],
    ["Xem tất cả", "View All"],
    ["Xem chi tiết", "View Details"],
    ["Trang chủ", "Home"],
    ["Bài tập", "Problems"],
    ["Cuộc thi", "Contests"],
    ["Xếp hạng", "Rankings"],
    ["Tổ chức & Câu lạc bộ", "Organizations & Clubs"],
    ["Tổ chức", "Organizations"],
    ["Bài nộp", "Submissions"],
    ["Luyện tập", "Practice"],
    ["Bảng Điều Khiển Quản Trị Tổ Chức", "Organization Admin Dashboard"],
    ["Quản trị Tổ chức", "Organization Admin"],
    ["Tham gia tổ chức", "Join Organization"],
    ["Rời tổ chức", "Leave Organization"],
    ["ĐÃ XÁC MINH", "VERIFIED"],
    ["Quản trị", "Admin"],
    ["Đăng nhập", "Login"],
    ["Đăng ký", "Register"],
    ["Đăng xuất", "Logout"],
    ["Tài khoản", "Account"],
    ["Hồ sơ", "Profile"],
    ["Cài đặt", "Settings"],
    ["Giới thiệu", "About"],
    ["Trợ giúp", "Help"],
    ["Quy chế thi", "Contest Rules"],
    ["Quy chế", "Rules"],
    ["Bảo mật", "Privacy"],
    ["Tìm kiếm", "Search"],
    ["Lọc kết quả", "Filter Results"],
    ["Đặt lại", "Reset"],
    ["Nộp bài", "Submit"],
    ["Chạy thử", "Run Code"],
    ["Làm mới", "Refresh"],
    ["Chấm lại", "Rejudge"],
    ["Sao chép", "Copy"],
    ["Đã chép!", "Copied!"],
    ["Đã sao chép!", "Copied!"],
    ["Lưu thay đổi", "Save Changes"],
    ["Lưu", "Save"],
    ["Hủy bỏ", "Cancel"],
    ["Đóng", "Close"],
    ["Trước", "Previous"],
    ["Sau", "Next"],
    ["Trang trước", "Previous"],
    ["Trang sau", "Next"],
    ["Tất cả", "All"],

    // Filter Dropdowns
    ["Tất cả độ khó", "All Difficulties"],
    ["Tất cả trạng thái", "All Statuses"],
    ["Tất cả ngôn ngữ", "All Languages"],
    ["Tất cả kết quả", "All Verdicts"],
    ["Tất cả quốc gia", "All Countries"],
    ["Dễ (≤ 50 điểm)", "Easy (≤ 50 pts)"],
    ["Trung bình (51 - 100 điểm)", "Medium (51 - 100 pts)"],
    ["Khó (> 100 điểm)", "Hard (> 100 pts)"],
    ["Đã giải (AC)", "Solved (AC)"],
    ["Đã thử nhưng chưa AC", "Attempted (Unsolved)"],
    ["Chưa thử", "Unattempted"],
    ["Mã bài (A-Z)", "Code (A-Z)"],
    ["Điểm giảm dần", "Points (High-Low)"],
    ["Điểm tăng dần", "Points (Low-High)"],
    ["Tỷ lệ giải cao nhất", "Highest AC Rate"],
    ["Chủ đề:", "Topics:"],
    ["Chủ đề", "Topics"],

    // Table Column Headers
    ["Tên bài toán & Phân loại", "Problem Title & Tags"],
    ["Tên bài toán", "Problem Title"],
    ["Tên bài tập", "Problem Title"],
    ["Tên bài", "Title"],
    ["Mã bài", "Code"],
    ["Độ khó", "Difficulty"],
    ["Điểm số", "Score"],
    ["Điểm", "Points"],
    ["Tỉ lệ AC", "AC Rate"],
    ["Tỷ lệ AC", "AC Rate"],
    ["Giới hạn", "Limits"],
    ["Thao tác", "Action"],
    ["Thành viên", "Member"],
    ["Người nộp", "Author"],
    ["Thời gian", "Time"],
    ["Bộ nhớ", "Memory"],
    ["Ngôn ngữ", "Language"],
    ["Trạng thái", "Status"],
    ["Kết quả", "Verdict"],
    ["Hạng", "Rank"],
    ["Tổng thể", "Overall"],
    ["Quốc gia", "Country"],
    ["Trường học", "School"],
    ["Tổ chức", "Organization"],

    // Verdicts & Statuses
    ["Chấp nhận (AC)", "Accepted (AC)"],
    ["Sai kết quả (WA)", "Wrong Answer (WA)"],
    ["Quá thời gian (TLE)", "Time Limit Exceeded (TLE)"],
    ["Quá bộ nhớ (MLE)", "Memory Limit Exceeded (MLE)"],
    ["Lỗi biên dịch (CE)", "Compilation Error (CE)"],
    ["Lỗi thực thi (RTE)", "Runtime Error (RTE)"],
    ["Đang chờ chấm...", "Pending..."],
    ["Đang chấm...", "Judging..."],
    ["Chấp nhận", "Accepted"],
    ["Sai kết quả", "Wrong Answer"],
    ["Quá thời gian", "Time Limit Exceeded"],
    ["Quá bộ nhớ", "Memory Limit Exceeded"],
    ["Lỗi biên dịch", "Compilation Error"],
    ["Lỗi thực thi", "Runtime Error"],
    ["Đang chờ chấm", "Pending"],
    ["Đang chấm", "Judging"],
    ["Chưa nộp", "Not Submitted"],
    ["Chưa giải", "Unsolved"],
    ["Đã giải", "Solved"],
    ["Đã thử", "Attempted"],

    // Difficulty Levels
    ["Chuyên gia", "Expert"],
    ["Trung bình", "Medium"],
    ["Khó", "Hard"],
    ["Dễ", "Easy"],

    // Form inputs & Placeholders
    ["Tìm kiếm theo mã bài (SUMA, MAXSUM...), tên bài...", "Search problems by code, title..."],
    ["Tìm kiếm bài tập...", "Search problems..."],
    ["Tìm kiếm thành viên hoặc trường...", "Search member or school..."],
    ["Mã bài (vd: SUMA)", "Problem code (e.g. SUMA)"],
    ["Tên tài khoản", "Username"],
    ["Mật khẩu", "Password"],
    ["Nhập lại mật khẩu", "Confirm Password"],
    ["Địa chỉ email", "Email Address"],
    ["Họ và tên", "Full Name"],
    ["Đăng ký ngay", "Register now"],
    ["Đăng nhập ngay", "Login now"],
    ["Quên mật khẩu?", "Forgot password?"],
    ["Chưa có tài khoản?", "Don't have an account?"],
    ["Đã có tài khoản?", "Already have an account?"],

    // Misc
    ["Đang tải bài tập...", "Loading problems..."],
    ["Đang tải xếp hạng...", "Loading rankings..."],
    ["Đang tải kỳ thi...", "Loading contest..."],
    ["Đang tải...", "Loading..."]
  ];

  // Map for fast exact lookup and regex matching
  const VI_TO_EN = new Map();
  const EN_TO_VI = new Map();

  PHRASE_PAIRS.forEach(([vi, en]) => {
    VI_TO_EN.set(vi.trim(), en.trim());
    EN_TO_VI.set(en.trim(), vi.trim());
  });

  // Regex pattern for whole phrases (greedy: longer phrases first)
  const sortedViPhrases = PHRASE_PAIRS
    .map(([vi]) => vi.trim())
    .sort((a, b) => b.length - a.length);

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  const viRegex = new RegExp(
    sortedViPhrases.map(p => escapeRegExp(p)).join('|'),
    'g'
  );

  const sortedEnPhrases = PHRASE_PAIRS
    .map(([, en]) => en.trim())
    .sort((a, b) => b.length - a.length);

  const enRegex = new RegExp(
    sortedEnPhrases.map(p => escapeRegExp(p)).join('|'),
    'g'
  );

  // ══════════════════════════════════════════════════════════════════════
  // 2. CORE TRANSLATION HELPERS
  // ══════════════════════════════════════════════════════════════════════
  function getLang() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED_LANGS.includes(saved)) {
      return saved;
    }
    return 'vi';
  }

  function translateString(str, targetLang) {
    if (!str || typeof str !== 'string') return str;
    const trimmed = str.trim();
    if (!trimmed) return str;

    if (targetLang === 'en') {
      if (VI_TO_EN.has(trimmed)) {
        return str.replace(trimmed, VI_TO_EN.get(trimmed));
      }
      return str.replace(viRegex, match => VI_TO_EN.get(match) || match);
    } else {
      if (EN_TO_VI.has(trimmed)) {
        return str.replace(trimmed, EN_TO_VI.get(trimmed));
      }
      return str.replace(enRegex, match => EN_TO_VI.get(match) || match);
    }
  }

  // ══════════════════════════════════════════════════════════════════════
  // 3. FULL RECURSIVE DOM TREE WALKER (TRANSLATES EVERYTHING)
  // ══════════════════════════════════════════════════════════════════════
  const IGNORED_TAGS = new Set([
    'SCRIPT', 'STYLE', 'CODE', 'PRE', 'SVG', 'CP-ICON', 'NOSCRIPT', 'TEXTAREA'
  ]);

  function translateNode(node, lang) {
    if (!node) return;

    // Skip ignored tags
    if (node.nodeType === Node.ELEMENT_NODE) {
      if (IGNORED_TAGS.has(node.tagName)) {
        // If it's a textarea, translate placeholder
        if (node.tagName === 'TEXTAREA' && node.placeholder) {
          if (!node._cp_vi_ph) node._cp_vi_ph = node.placeholder;
          node.placeholder = lang === 'en' ? translateString(node._cp_vi_ph, 'en') : node._cp_vi_ph;
        }
        return;
      }

      // Translate attributes: placeholder, title, aria-label
      if (node.hasAttribute('placeholder')) {
        if (!node._cp_vi_ph) node._cp_vi_ph = node.getAttribute('placeholder');
        node.setAttribute('placeholder', lang === 'en' ? translateString(node._cp_vi_ph, 'en') : node._cp_vi_ph);
      }

      if (node.hasAttribute('title')) {
        if (!node._cp_vi_title) node._cp_vi_title = node.getAttribute('title');
        node.setAttribute('title', lang === 'en' ? translateString(node._cp_vi_title, 'en') : node._cp_vi_title);
      }

      // Handle Select Options
      if (node.tagName === 'OPTION') {
        if (!node._cp_vi_text) node._cp_vi_text = node.textContent;
        node.textContent = lang === 'en' ? translateString(node._cp_vi_text, 'en') : node._cp_vi_text;
        return;
      }
    }

    // Translate Text Node
    if (node.nodeType === Node.TEXT_NODE) {
      const val = node.nodeValue;
      if (val && val.trim().length > 0) {
        // Save initial Vietnamese baseline text
        if (!node._cp_vi) {
          node._cp_vi = val;
        }

        if (lang === 'en') {
          node.nodeValue = translateString(node._cp_vi, 'en');
        } else {
          node.nodeValue = node._cp_vi;
        }
      }
      return;
    }

    // Traverse children
    let child = node.firstChild;
    while (child) {
      translateNode(child, lang);
      child = child.nextSibling;
    }
  }

  let isTranslating = false;

  function translateDOM(root = document.body) {
    if (isTranslating || !root) return;
    isTranslating = true;

    try {
      const lang = getLang();
      document.documentElement.lang = lang;

      translateNode(root, lang);
      updateToggleButtons();

      window.dispatchEvent(new CustomEvent('cp-lang-changed', { detail: { lang } }));
    } finally {
      isTranslating = false;
    }
  }

  function setLang(lang) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = 'vi';
    localStorage.setItem(STORAGE_KEY, lang);
    translateDOM();
  }

  function toggleLang() {
    const current = getLang();
    const nextLang = current === 'vi' ? 'en' : 'vi';
    setLang(nextLang);
    return nextLang;
  }

  function updateToggleButtons() {
    const lang = getLang();
    const buttons = document.querySelectorAll('.cp-lang-toggle, [data-lang-toggle]');
    buttons.forEach(btn => {
      btn.setAttribute('title', lang === 'vi' ? 'Chuyển sang English' : 'Switch to Tiếng Việt');
      btn.dataset.currentLang = lang;

      const textWrap = btn.querySelector('.lang-text');
      if (textWrap) {
        textWrap.textContent = lang.toUpperCase();
      } else {
        btn.textContent = lang === 'vi' ? 'VI' : 'EN';
      }
    });
  }

  // ══════════════════════════════════════════════════════════════════════
  // 4. MUTATION OBSERVER (AUTO-TRANSLATE NEW AJAX / DYNAMIC DATA)
  // ══════════════════════════════════════════════════════════════════════
  function setupMutationObserver() {
    if (!window.MutationObserver) return;

    let debounceTimer = null;
    const observer = new MutationObserver(mutations => {
      if (getLang() !== 'en') return;
      if (isTranslating) return;

      let hasNewNodes = false;
      for (const m of mutations) {
        if (m.type === 'childList' && m.addedNodes.length > 0) {
          for (const n of m.addedNodes) {
            if (n.nodeType === Node.ELEMENT_NODE && !IGNORED_TAGS.has(n.tagName)) {
              hasNewNodes = true;
              break;
            }
          }
        }
        if (hasNewNodes) break;
      }

      if (hasNewNodes) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          translateDOM();
        }, 120);
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  // ══════════════════════════════════════════════════════════════════════
  // 5. INITIALIZATION
  // ══════════════════════════════════════════════════════════════════════
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      translateDOM();
      setupMutationObserver();
    });
  } else {
    translateDOM();
    setupMutationObserver();
  }

  window.CPI18n = {
    getLang,
    setLang,
    toggleLang,
    t: (key, fallback) => translateString(fallback !== undefined ? fallback : key, getLang()),
    translateDOM,
    updateButtons: updateToggleButtons
  };
})();
