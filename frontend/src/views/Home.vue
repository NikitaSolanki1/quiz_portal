<template>
  <Navbar />
  <main class="home">
    <section class="hero">
      <p class="eyebrow">Exam zone desk</p>
      <h1>Manage courses, viva slots, and marks in ExamZone</h1>
      <p class="lead">
        ExamZone lets staff create courses, schedule exams, open booking windows,
        and record viva marks for every student.
      </p>
      <div class="actions">
        <a class="btn primary" href="/login">Login</a>
        <a class="btn" href="/register">Register</a>
      </div>
    </section>

    <section class="details">
      <h2>What you can manage</h2>
      <div class="cards">
        <article>
          <h3>Courses</h3>
          <p>Create a course with a name, description, and duration in hours.</p>
          <a href="/manage_course">Manage courses</a>
        </article>
        <article>
          <h3>Examinations</h3>
          <p>
            Schedule an exam against a course, set examiner slot dates, booking
            windows, and the exam start and end dates.
          </p>
          <a href="/manage_examination">Manage examinations</a>
        </article>
        <article>
          <h3>Examiners</h3>
          <p>Add examiner accounts and block or unblock access when needed.</p>
          <a href="/manage_examinor">Manage examiners</a>
        </article>
        <article>
          <h3>Question bank</h3>
          <p>Add questions and marks for a specific examination from its row.</p>
          <a href="/manage_examination">Open an examination</a>
        </article>
      </div>
    </section>

    <section class="roles">
      <h2>Who uses it</h2>
      <ul>
        <li><strong>Admin</strong> — creates courses, examinations, and examiner accounts.</li>
        <li><strong>Examiner</strong> — is assigned to an exam and can be blocked from login.</li>
        <li><strong>Student</strong> — registers with a name, email, and password.</li>
      </ul>
    </section>
  </main>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
</script>

<style scoped>
.home {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}

.hero {
  background: #2f5d50;
  color: #fff;
  padding: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  color: #ddd;
}

h1 {
  margin: 0 0 10px;
  font-size: 28px;
}

.lead {
  margin: 0 0 16px;
  max-width: 600px;
}

.actions {
  display: flex;
  gap: 10px;
}

.btn {
  display: inline-block;
  padding: 8px 14px;
  text-decoration: none;
  background: #fff;
  color: #2f5d50;
  font-weight: bold;
}

.btn.primary {
  background: #dcece6;
  color: #244a40;
}

.details,
.roles {
  margin-top: 24px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

article {
  border: 1px solid #ccc;
  padding: 12px;
  background: #fff;
}

article h3 {
  margin: 0 0 8px;
}

article p {
  margin: 0 0 10px;
}

article a,
.roles a {
  color: #333;
}

.roles ul {
  margin: 0;
  padding-left: 18px;
}
</style>
