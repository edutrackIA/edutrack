# ADR-0011: Invitaciones por correo para que los apoderados creen su contraseña

- **Estado:** Aceptado
- **Fecha:** 2026-10-30

## Contexto
Los apoderados se registran desde la ficha del estudiante o con una importación masiva. Si el colegio les asignara una contraseña, tendría que enviarla por un canal inseguro (WhatsApp, papel) y conocería la clave de cada familia.

## Decisión
- Al registrar un apoderado nuevo se crea su cuenta **sin contraseña** (`password_hash` nulo) y se le envía un **enlace de un solo uso** para crearla.
- El enlace usa un token aleatorio de 256 bits. En la base de datos solo se guarda su **SHA-256**, de modo que una filtración no expone enlaces válidos.
- El enlace vence a los **7 días**. Reenviar la invitación revoca los enlaces anteriores.
- La contraseña debe tener al menos 8 caracteres, una letra y un número.
- Un mismo correo con rol de apoderado se reutiliza para varios hijos. Un correo que pertenece a personal del colegio se rechaza.
- En la importación, los correos se envían **después** de guardar las filas; una vista previa nunca envía nada.
- Mientras no acepte, el login responde igual que con credenciales incorrectas, para no revelar qué cuentas existen. Aun así, la familia ya recibe los correos informativos.

## Consecuencias
- El colegio nunca conoce ni transmite contraseñas.
- Hace falta un servidor de correo operativo; si el envío falla, la invitación se puede reenviar desde la ficha.
