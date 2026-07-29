frappe.ready(() => {
	const form = document.querySelector("[data-complaint-form]");
	form?.addEventListener("submit", (event) => {
		event.preventDefault();
		frappe.call({method:"consultation_center.api.support_portal.create_complaint",type:"POST",args:Object.fromEntries(new FormData(form).entries()),callback:(response)=>{form.querySelector("[data-form-message]").textContent=response.message.message;setTimeout(()=>location.reload(),500);},error:()=>{form.querySelector("[data-form-message]").textContent="تعذر إرسال البلاغ";}});
	});
	const support = document.querySelector("[data-support-form]");
	support?.addEventListener("submit", (event) => {
		event.preventDefault();
		frappe.call({method:"consultation_center.api.support_portal.create_support_ticket",type:"POST",args:Object.fromEntries(new FormData(support).entries()),callback:(response)=>{support.querySelector("[data-form-message]").textContent=response.message.message;setTimeout(()=>location.reload(),500);},error:()=>{support.querySelector("[data-form-message]").textContent="تعذر إرسال طلب الدعم";}});
	});
});
