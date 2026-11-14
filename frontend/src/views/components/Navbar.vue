<template>
  <nav>
    <div class="nav-brand">ExamNest</div>
    <div class="nav-links">
      <template v-if="loggedIn">
        <template v-if="role === 'admin'">
          <a href="/admin">Home</a>
          <a href="/manage_course" >Courses</a>
          <a href="/manage_examination" >Examinations</a>
          <a href="/manage_examinor" >Examiners</a>
          <a href="/all_slots" >Slots</a>
          <a href="/manage_students" >Students</a>
          <a href="/manage_bookings" >Bookings</a>
          <a href="/reports" >Reports</a>
          <a href="/admin_search" >Search</a>
        </template>

        <template v-else-if="role === 'examinor'">
          <a href="/examinor" >Home</a>
          <a href="/assigned_examination" >Assigned Examination</a>
          <a href="/view_booking" >View Booking</a>
        </template>

        <template v-else>
          <a href="/user" >Home</a>
          <a href="/see_examination" >Examinations</a>
          <a href="/my_booking" >My Bookings</a>
          <a href="/my_results" >Results</a>
        </template>

        <button class="logout-btn" @click.prevent="logout">Logout</button>
      </template>

      <template v-else>
        <a href="/login" >Login</a>
        <a href="/register" >Signup</a>
      </template>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'

const loggedIn = ref(!!localStorage.getItem('token'))
const role = ref(localStorage.getItem('role') || '')

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('name')
  localStorage.removeItem('user_id')
  loggedIn.value = false
  role.value = ''
  window.location.href = '/login'
}
</script>

<style scoped>
nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  background: #333;
  color: #fff;
}
.nav-brand {
  font-weight: bold;
  font-size: 18px;
}
.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
a {
  color: #eee;
  text-decoration: none;
  font-size: 14px;
}
a:hover {
  text-decoration: underline;
}
.logout-btn {
  background: #a00;
  color: #fff;
  border: none;
  padding: 6px 10px;
  cursor: pointer;
}
</style>
