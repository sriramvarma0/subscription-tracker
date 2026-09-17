document.addEventListener('DOMContentLoaded', () => {
  // Auto-detect and sync client timezone cookie with server
  (function syncClientTimezone() {
    try {
      const userTZ = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const match = document.cookie.match(/(?:^|; )user_timezone=([^;]*)/);
      const currentCookieTZ = match ? decodeURIComponent(match[1]) : null;
      if (userTZ && currentCookieTZ !== userTZ) {
        document.cookie = `user_timezone=${encodeURIComponent(userTZ)}; path=/; max-age=31536000; SameSite=Lax`;
        if (currentCookieTZ === null) {
          window.location.reload();
        }
      }
    } catch (e) {
      console.warn('Timezone detection error:', e);
    }
  })();

  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Sponsor & Cost toggle logic
  const isSponsoredCheckbox = document.getElementById('is_sponsored');
  const sponsorContainer = document.getElementById('sponsorFields');
  const sponsorCompanyInput = document.getElementById('sponsor_company');
  const costContainer = document.getElementById('costGroup');
  const costInput = document.getElementById('cost');
  const costReqStar = document.getElementById('costReqStar');

  function updateSponsorFields() {
    const isSponsored = isSponsoredCheckbox ? isSponsoredCheckbox.checked : false;
    if (isSponsored) {
      if (sponsorContainer) sponsorContainer.classList.remove('hidden');
      if (sponsorCompanyInput) sponsorCompanyInput.required = true;
      if (costContainer) costContainer.classList.add('hidden');
      if (costInput) {
        costInput.value = '';
        costInput.required = false;
      }
      if (costReqStar) costReqStar.style.display = 'none';
    } else {
      if (sponsorContainer) sponsorContainer.classList.add('hidden');
      if (sponsorCompanyInput) sponsorCompanyInput.required = false;
      if (costContainer) costContainer.classList.remove('hidden');
      if (costInput) costInput.required = true;
      if (costReqStar) costReqStar.style.display = 'inline';
    }
  }

  if (isSponsoredCheckbox) {
    isSponsoredCheckbox.addEventListener('change', updateSponsorFields);
  }

  // No Expiry checkbox toggle logic
  const noExpiryCheckbox = document.getElementById('no_expiry');
  const endDateInput = document.getElementById('end_date');
  const endDateStar = document.getElementById('endDateReqStar');

  function updateExpiryFields() {
    if (!endDateInput) return;
    const isNoExpiry = noExpiryCheckbox ? noExpiryCheckbox.checked : false;
    if (isNoExpiry) {
      endDateInput.disabled = true;
      endDateInput.value = '';
      endDateInput.required = false;
      if (endDateStar) endDateStar.style.display = 'none';
    } else {
      endDateInput.disabled = false;
      endDateInput.required = true;
      if (endDateStar) endDateStar.style.display = 'inline';
    }
  }

  if (noExpiryCheckbox) {
    noExpiryCheckbox.addEventListener('change', updateExpiryFields);
  }

  // Modal Open / Close logic
  const subModal = document.getElementById('subscriptionModal');
  const deleteModal = document.getElementById('deleteModal');
  const subForm = document.getElementById('subscriptionForm');
  const modalTitle = document.getElementById('modalTitle');

  window.openAddModal = function () {
    if (!subModal || !subForm) return;
    modalTitle.textContent = 'Add Subscription';
    subForm.action = '/subscriptions';
    subForm.reset();
    document.getElementById('subId').value = '';
    const autoRenewNo = document.getElementById('autorenew_no');
    if (autoRenewNo) autoRenewNo.checked = true;
    if (noExpiryCheckbox) noExpiryCheckbox.checked = false;
    if (isSponsoredCheckbox) isSponsoredCheckbox.checked = false;
    const currencyEl = document.getElementById('currency');
    if (currencyEl) currencyEl.value = 'USD';
    updateExpiryFields();
    updateSponsorFields();
    subModal.classList.add('active');
  };

  window.openEditModal = function (subId) {
    if (!subModal || !subForm) return;
    modalTitle.textContent = 'Edit Subscription';
    subForm.action = `/subscriptions/${subId}/edit`;

    fetch(`/subscriptions/${subId}`, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(res => res.json())
      .then(data => {
        if (data.subscription) {
          const s = data.subscription;
          document.getElementById('subId').value = s.id;
          document.getElementById('company_name').value = s.company_name || '';
          document.getElementById('subscription_name').value = s.subscription_name || '';
          document.getElementById('account').value = s.account || '';
          document.getElementById('start_date').value = s.start_date || '';
          document.getElementById('end_date').value = s.end_date || '';
          document.getElementById('cost').value = (s.cost !== null && s.cost !== undefined) ? s.cost : '';
          const currencyEl = document.getElementById('currency');
          if (currencyEl) currencyEl.value = s.currency || 'USD';

          if (noExpiryCheckbox) noExpiryCheckbox.checked = !s.end_date;

          if (s.auto_renew === 'YES') {
            const el = document.getElementById('autorenew_yes'); if (el) el.checked = true;
          } else {
            const el = document.getElementById('autorenew_no'); if (el) el.checked = true;
          }

          if (isSponsoredCheckbox) isSponsoredCheckbox.checked = !!s.is_sponsored;

          document.getElementById('sponsor_company').value = s.sponsor_company || '';
          document.getElementById('sponsor_account').value = s.sponsor_account || '';
          document.getElementById('note').value = s.note || '';

          updateExpiryFields();
          updateSponsorFields();
          subModal.classList.add('active');
        }
      })
      .catch(err => {
        alert('Failed to load subscription details.');
      });
  };

  window.closeSubModal = function () {
    if (subModal) subModal.classList.remove('active');
  };

  // Renewal Modal logic
  const renewModal = document.getElementById('renewModal');
  const renewForm = document.getElementById('renewForm');
  const renewModalTitle = document.getElementById('renewModalTitle');

  window.openRenewModal = function (subId, renewalType, prevExpiry, currentAutoRenew) {
    if (!renewModal || !renewForm) return;
    renewalType = renewalType || 'MANUAL';
    if (renewModalTitle) {
      renewModalTitle.textContent = renewalType === 'AUTO' ? 'Confirm Auto-Renewal' : 'Renew Subscription';
    }
    renewForm.action = `/subscriptions/${subId}/renew`;
    document.getElementById('renewSubId').value = subId;
    document.getElementById('renewalTypeInput').value = renewalType;

    const prevExpiryEl = document.getElementById('renewPrevExpiry');
    if (prevExpiryEl) prevExpiryEl.textContent = prevExpiry || 'None';

    // Default new_start_date to prevExpiry or today
    const todayStr = new Date().toISOString().split('T')[0];
    document.getElementById('new_start_date').value = prevExpiry || todayStr;
    document.getElementById('new_end_date').value = '';
    document.getElementById('renewal_note').value = '';

    if (currentAutoRenew === 'YES') {
      const el = document.getElementById('renew_autorenew_yes'); if (el) el.checked = true;
    } else {
      const el = document.getElementById('renew_autorenew_no'); if (el) el.checked = true;
    }

    renewModal.classList.add('active');
  };

  window.closeRenewModal = function () {
    if (renewModal) renewModal.classList.remove('active');
  };

  window.dismissAutoRenewBanner = function (subId, prevExpiry, currentAutoRenew) {
    const banner = document.getElementById(`autoRenewBanner-${subId}`);
    if (banner) {
      banner.style.display = 'none';
    }
    const container = document.getElementById(`renewBtnContainer-${subId}`);
    if (container) {
      container.innerHTML = `<button type="button" class="btn btn-secondary btn-sm" onclick="openRenewModal(${subId}, 'MANUAL', '${prevExpiry || ''}', '${currentAutoRenew || ''}')" title="Renew"><i data-lucide="refresh-cw" style="width:14px; height:14px;"></i> <span>Renew</span></button>`;
      if (window.lucide) window.lucide.createIcons();
    }
  };

  window.toggleRenewalHistory = function (subId) {
    const list = document.getElementById(`historyList-${subId}`);
    const toggleBtn = document.getElementById(`historyToggle-${subId}`);
    if (list) {
      if (list.classList.contains('hidden')) {
        list.classList.remove('hidden');
        if (toggleBtn) toggleBtn.querySelector('span').textContent = toggleBtn.querySelector('span').textContent.replace('View', 'Hide');
      } else {
        list.classList.add('hidden');
        if (toggleBtn) toggleBtn.querySelector('span').textContent = toggleBtn.querySelector('span').textContent.replace('Hide', 'View');
      }
    }
  };

  window.openDeleteModal = function (subId, companyName) {
    if (!deleteModal) return;
    const deleteForm = document.getElementById('deleteForm');
    const deleteCompName = document.getElementById('deleteCompanyName');
    deleteForm.action = `/subscriptions/${subId}/delete`;
    deleteCompName.textContent = companyName;
    deleteModal.classList.add('active');
  };

  window.closeDeleteModal = function () {
    if (deleteModal) deleteModal.classList.remove('active');
  };

  // Close modals on clicking overlay background
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        overlay.classList.remove('active');
      }
    });
  });

  // Filter & Search Controls
  const filterPills = document.querySelectorAll('.pill-btn');
  const sortSelect = document.getElementById('sortSelect');
  const searchInput = document.getElementById('searchInput');

  function updateDashboardParams(newParams) {
    const url = new URL(window.location.href);
    Object.keys(newParams).forEach(key => {
      if (newParams[key]) {
        url.searchParams.set(key, newParams[key]);
      } else {
        url.searchParams.delete(key);
      }
    });
    window.location.href = url.toString();
  }

  window.filterByStatus = function (status) {
    updateDashboardParams({ filter: status });
  };

  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      updateDashboardParams({ sort: e.target.value });
    });
  }

  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        updateDashboardParams({ q: searchInput.value });
      }
    });
  }

  // JSON Import Trigger
  window.triggerImportJSON = function () {
    const fileInput = document.getElementById('importFileInput');
    if (fileInput) fileInput.click();
  };

  window.submitImportForm = function () {
    const importForm = document.getElementById('importForm');
    if (importForm) importForm.submit();
  };
});
