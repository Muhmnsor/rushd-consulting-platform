frappe.ready(() => {
	const showMessage = (form, text, type = "info") => {
		const message = form?.querySelector("[data-form-message]");
		if (!message) return;
		message.textContent = text;
		message.className = `rushd-form-message is-visible is-${type}`;
	};
	const errorMessage = (error) => {
		try {
			return JSON.parse(error?._server_messages || "[]")
				.map((item) => JSON.parse(item).message)
				.join(" ") || error.message;
		} catch {
			return error?.message || "تعذر حفظ التغييرات. تحقق من الحقول وحاول مجددًا.";
		}
	};
	const call = (method, args) => new Promise((resolve, reject) => {
		frappe.call({method, type: "POST", args, callback: (response) => resolve(response.message), error: reject});
	});

	const profileForm = document.querySelector("[data-professional-profile-form]");
	const repeatableFields = profileForm?.querySelectorAll("[data-repeatable-field]") || [];
	const syncRepeatableField = (field) => {
		const values = [...field.querySelectorAll("[data-repeatable-input]")]
			.map((input) => input.value.trim())
			.filter(Boolean);
		field.querySelector("[data-repeatable-output]").value = values.join("\n");
	};
	const syncRepeatableFields = () => repeatableFields.forEach(syncRepeatableField);
	const createRepeatableRow = (field) => {
		const referenceInput = field.querySelector("[data-repeatable-input]");
		const row = document.createElement("div");
		row.className = "rushd-repeatable-row";
		row.dataset.repeatableRow = "";
		const input = document.createElement("input");
		input.type = "text";
		input.dataset.repeatableInput = "";
		input.placeholder = field.dataset.placeholder || "اكتب القيمة";
		input.maxLength = referenceInput?.maxLength > 0 ? referenceInput.maxLength : 500;
		const remove = document.createElement("button");
		remove.type = "button";
		remove.dataset.removeRepeatable = "";
		remove.setAttribute("aria-label", "حذف العنصر");
		remove.textContent = "×";
		row.append(input, remove);
		return row;
	};

	const updateProfileCompleteness = () => {
		if (!profileForm) return;
		syncRepeatableFields();
		const checks = [
			profileForm.elements.profile_image?.value,
			profileForm.elements.specializations?.value,
			profileForm.elements.languages?.value,
			profileForm.elements.qualifications?.value,
			profileForm.elements.experience_summary?.value,
			profileForm.elements.public_title?.value,
			profileForm.elements.public_bio?.value,
			profileForm.elements.licenses?.value,
			profileForm.elements.suitable_groups?.value,
		];
		const completed = checks.filter((value) => String(value || "").trim()).length;
		const value = Math.round((completed / checks.length) * 100);
		const output = document.querySelector("[data-profile-completeness-value]");
		if (output) output.textContent = `${value}%`;
	};

	repeatableFields.forEach((field) => {
		field.querySelector("[data-add-repeatable]")?.addEventListener("click", () => {
			const row = createRepeatableRow(field);
			field.querySelector("[data-repeatable-list]").append(row);
			row.querySelector("input").focus();
		});
		field.addEventListener("click", (event) => {
			const button = event.target.closest("[data-remove-repeatable]");
			if (!button) return;
			const list = field.querySelector("[data-repeatable-list]");
			const rows = list.querySelectorAll("[data-repeatable-row]");
			if (rows.length === 1) rows[0].querySelector("input").value = "";
			else button.closest("[data-repeatable-row]").remove();
			syncRepeatableField(field);
			updateProfileCompleteness();
		});
		field.addEventListener("input", () => {
			syncRepeatableField(field);
			updateProfileCompleteness();
		});
	});

	const imageInput = profileForm?.querySelector("[data-profile-image-file]");
	const imageUrl = profileForm?.querySelector("[data-profile-image-url]");
	const imagePreview = profileForm?.querySelector("[data-profile-image-preview]");
	const imageElement = imagePreview?.querySelector("img");
	const imagePlaceholder = imagePreview?.querySelector("span");
	const imageMessage = profileForm?.querySelector("[data-profile-image-message]");
	const removeImageButton = profileForm?.querySelector("[data-remove-profile-image]");
	let previewObjectUrl = null;

	const setImageMessage = (text, type = "") => {
		if (!imageMessage) return;
		imageMessage.textContent = text;
		imageMessage.classList.remove("is-error", "is-success");
		if (type) imageMessage.classList.add(`is-${type}`);
	};
	const inspectProfileImage = (file) => new Promise((resolve) => {
		imageInput.setCustomValidity("");
		if (!file) return resolve(true);
		if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
			imageInput.setCustomValidity("اختر صورة بصيغة JPG أو PNG أو WebP");
			setImageMessage(imageInput.validationMessage, "error");
			return resolve(false);
		}
		if (file.size > 2 * 1024 * 1024) {
			imageInput.setCustomValidity("حجم الصورة يجب ألا يتجاوز 2 ميجابايت");
			setImageMessage(imageInput.validationMessage, "error");
			return resolve(false);
		}
		const objectUrl = URL.createObjectURL(file);
		const image = new Image();
		image.onload = () => {
			const ratio = image.naturalWidth / image.naturalHeight;
			if (image.naturalWidth < 600 || image.naturalHeight < 600) {
				imageInput.setCustomValidity("أبعاد الصورة يجب ألا تقل عن 600 × 600 بكسل");
			} else if (ratio < .85 || ratio > 1.15) {
				imageInput.setCustomValidity("استخدم صورة مربعة تقريبًا حتى لا يُقص الوجه عند العرض");
			}
			if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
			previewObjectUrl = objectUrl;
			imageElement.src = objectUrl;
			imageElement.hidden = false;
			imagePlaceholder.hidden = true;
			removeImageButton.hidden = false;
			setImageMessage(
				imageInput.validationMessage || `جاهزة للرفع · ${image.naturalWidth} × ${image.naturalHeight} بكسل`,
				imageInput.validationMessage ? "error" : "success",
			);
			resolve(!imageInput.validationMessage);
		};
		image.onerror = () => {
			URL.revokeObjectURL(objectUrl);
			imageInput.setCustomValidity("تعذر قراءة الصورة المختارة");
			setImageMessage(imageInput.validationMessage, "error");
			resolve(false);
		};
		image.src = objectUrl;
	});

	imageInput?.addEventListener("change", async () => {
		const valid = await inspectProfileImage(imageInput.files?.[0]);
		if (!valid) imageInput.reportValidity();
	});
	removeImageButton?.addEventListener("click", () => {
		imageInput.value = "";
		imageInput.setCustomValidity("");
		imageUrl.value = "";
		imageElement.removeAttribute("src");
		imageElement.hidden = true;
		imagePlaceholder.hidden = false;
		removeImageButton.hidden = true;
		setImageMessage("ستظهر الأحرف الأولى من اسمك بعد الحفظ.");
		updateProfileCompleteness();
	});

	const uploadProfileImage = async () => {
		const file = imageInput?.files?.[0];
		if (!file) return;
		if (!(await inspectProfileImage(file))) throw new Error(imageInput.validationMessage);
		const upload = new FormData();
		upload.append("file", file, file.name);
		upload.append("is_private", "0");
		upload.append("folder", "Home/Attachments");
		const response = await fetch("/api/method/upload_file", {
			method: "POST",
			headers: {"X-Frappe-CSRF-Token": frappe.csrf_token},
			body: upload,
		});
		const payload = await response.json();
		const fileUrl = payload?.message?.file_url;
		if (!response.ok || !fileUrl) throw new Error(payload?.message || "تعذر رفع الصورة المهنية");
		imageUrl.value = fileUrl;
	};

	const publicTitle = profileForm?.elements.public_title;
	const publicBio = profileForm?.elements.public_bio;
	const updatePublicPreview = () => {
		const previewTitle = profileForm?.querySelector("[data-preview-title]");
		const previewBio = profileForm?.querySelector("[data-preview-bio]");
		const bioCount = profileForm?.querySelector("[data-bio-count]");
		if (previewTitle) previewTitle.textContent = publicTitle.value.trim() || "المسمى المهني";
		if (previewBio) previewBio.textContent = publicBio.value.trim() || "ستظهر هنا نبذة تعريفية قصيرة وواضحة للمستفيد.";
		if (bioCount) bioCount.textContent = publicBio.value.length;
	};
	publicTitle?.addEventListener("input", () => { updatePublicPreview(); updateProfileCompleteness(); });
	publicBio?.addEventListener("input", () => { updatePublicPreview(); updateProfileCompleteness(); });
	profileForm?.querySelectorAll("textarea, input").forEach((field) => {
		field.addEventListener("input", updateProfileCompleteness);
	});
	updatePublicPreview();
	updateProfileCompleteness();

	profileForm?.addEventListener("submit", async (event) => {
		event.preventDefault();
		const button = profileForm.querySelector("[type='submit']");
		button.disabled = true;
		showMessage(profileForm, imageInput?.files?.[0] ? "جارٍ رفع الصورة وحفظ الملف…" : "جارٍ حفظ الملف المهني…");
		try {
			syncRepeatableFields();
			await uploadProfileImage();
			const result = await call(
				"consultation_center.api.consultant_settings.save_professional_profile",
				Object.fromEntries(new FormData(profileForm).entries()),
			);
			showMessage(profileForm, result.message || "تم حفظ الملف المهني", "success");
			button.disabled = false;
			setTimeout(() => window.location.reload(), 650);
		} catch (error) {
			showMessage(profileForm, errorMessage(error), "error");
			button.disabled = false;
		}
	});

	const submitForm = (selector, method) => {
		const form = document.querySelector(selector);
		if (!form) return;
		form.addEventListener("submit", async (event) => {
			event.preventDefault();
			const button = form.querySelector("[type='submit']");
			button.disabled = true;
			try {
				const result = await call(method, Object.fromEntries(new FormData(form).entries()));
				showMessage(form, result.message || "تم الحفظ", "success");
				setTimeout(() => window.location.reload(), 500);
			} catch (error) {
				showMessage(form, errorMessage(error), "error");
				button.disabled = false;
			}
		});
	};

	submitForm("[data-availability-form]", "consultation_center.api.consultant_settings.save_availability_rule");
	submitForm("[data-time-off-form]", "consultation_center.api.consultant_settings.add_time_off");
	submitForm("[data-capacity-form]", "consultation_center.api.consultant_settings.update_capacity");
});
