# UA Parcel Tracker для Home Assistant

Інтеграція для відстеження посилок у Home Assistant.

> Статус: v0.2.0 у розробці. Підтримується Нова пошта; Укрпошта та Meest Express заплановані.

## Планована підтримка

- Нова пошта (працює, потрібен API-ключ з кабінету)
- Укрпошта
- Meest Express

## Встановлення через HACS (custom repository)

1. Відкрийте HACS → три крапки → **Custom repositories**.
2. Вкажіть URL репозиторію і оберіть категорію **Integration**.
3. Встановіть інтеграцію та перезавантажте Home Assistant.
4. Додайте інтеграцію: **Налаштування → Пристрої та служби → Додати інтеграцію → UA Parcel Tracker**.

## Розробка

Код знаходиться в `custom_components/ua_parcel_tracker/`. Перед релізом перевіряйте репозиторій командами або CI з `hassfest` і HACS-валідацією.

## Ліцензія

MIT, див. [LICENSE](LICENSE).
