document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // Sponsor toggle logic
  const sponsorRadios = document.querySelectorAll('input[name="is_sponsored"]');
  const sponsorContainer = document.getElementById('sponsorFields');
  const sponsorCompanyInput = document.getElementById('sponsor_company');

  function updateSponsorFields() {
    const isSponsored = document.querySelector('input[name="is_sponsored"]:checked')?.value === 'true';
    if (sponsorContainer) {
      if (isSponsored) {
        sponsorContainer.classList.remove('hidden');
        if (sponsorCompanyInput) sponsorCompanyInput.required = true;
      } else {
        sponsorContainer.classList.add('hidden');
        if (sponsorCompanyInput) sponsorCompanyInput.required = false;
      }
    }
  }

  sponsorRadios.forEach(radio => {
    radio.addEventListener('change', updateSponsorFields);
  });

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

          if (s.is_sponsored) {
            document.getElementById('sponsored_yes').checked = true;
          } else {
            document.getElementById('sponsored_no').checked = true;
          }

          document.getElementById('sponsor_company').value = s.sponsor_company || '';
          document.getElementById('sponsor_account').value = s.sponsor_account || '';
          document.getElementById('note').value = s.note || '';

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
