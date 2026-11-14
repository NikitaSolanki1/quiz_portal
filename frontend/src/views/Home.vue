<template>
  <Navbar />
  <main class="home">
    <section class="hero">
      <p class="eyebrow">Quiz portal desk</p>
      <h1>Quiz Portal for courses, viva booking, and results</h1>
      <p class="lead">
        Create quiz courses, schedule viva exams, and open booking slots.
        Students join, reserve a time, and view marks after publish.
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
