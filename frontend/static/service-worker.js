/*
 * This software is licensed under a dual license:
 *
 * 1. Creative Commons Attribution-NonCommercial (CC BY-NC)
 *    for individuals and open source projects.
 * 2. Commercial License for business use.
 *
 * For commercial inquiries, contact: license@tradiny.com
 */

self.addEventListener("push", function (event) {
  let data = event.data.json();

  const promiseChain = self.registration.showNotification(
    data.notification.title,
  );
  event.waitUntil(promiseChain);
});
