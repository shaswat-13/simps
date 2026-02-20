document.addEventListener("DOMContentLoaded", () => {
    const slider = document.querySelector(".amountSlider");
    const amountValue = document.querySelector(".amountValue");
    const buyBtn = document.getElementById("buyBtn");
    const skipBtn = document.getElementById("skipBtn");
    const form = document.getElementById("buyForm");
    const card = document.querySelector(".card");

    if (!slider || !card) return;


    const slideDirection = sessionStorage.getItem("slideDirection");

    function triggerSlideIn(direction) {
        const enteringClass =
            direction === "from-right"
                ? "entering-from-right"
                : "entering-from-left";

        const slideClass =
            direction === "from-right"
                ? "slide-in-from-right"
                : "slide-in-from-left";

        card.classList.add(enteringClass);

        card.getBoundingClientRect();

        card.classList.remove(enteringClass);
        card.classList.add(slideClass);


        card.addEventListener(
            "animationend",
            (e) => {
                if (
                    e.animationName !== "slide-in-from-right" &&
                    e.animationName !== "slide-in-from-left"
                ) return;

                card.classList.remove(slideClass);
            },
            { once: true }
        );
    }

    if (slideDirection === "from-right" || slideDirection === "from-left") {
        triggerSlideIn(slideDirection);
        sessionStorage.removeItem("slideDirection");
    }


    slider.addEventListener("input", () => {
        amountValue.textContent = slider.value;
    });

    function animateThen(cls, callback) {
        const expected =
            cls === "swipe-left" ? "swipe-left" : "swipe-right";

        card.classList.add(cls);

        card.addEventListener(
            "animationend",
            (e) => {
                if (e.animationName !== expected) return;

                // optional: hide so no ghost frame
                card.style.display = "none";

                callback?.();
            },
            { once: true }
        );
    }


    buyBtn.addEventListener("click", async () => {
        if (buyBtn.disabled) return;
        buyBtn.disabled = true;

        sessionStorage.setItem("slideDirection", "from-left");

        animateThen("swipe-right", async () => {
            const formData = new FormData(form);
            formData.set("amount", slider.value);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": document.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        ).value,
                    },
                });

                if (response.ok) {
                    window.location.href = "/explore/";
                } else {
                    const data = await response.json();
                    sessionStorage.removeItem("slideDirection");
                    alert("⚠️ " + (data.error || "Insufficient funds."));
                    buyBtn.disabled = false;
                }
            } catch (err) {
                console.error(err);
                sessionStorage.removeItem("slideDirection");
                alert("Unexpected error occurred.");
                buyBtn.disabled = false;
            }
        });
    });



    skipBtn.addEventListener("click", () => {
        sessionStorage.setItem("slideDirection", "from-right");

        animateThen("swipe-left", () => {
            window.location.reload();
        });
    });
});