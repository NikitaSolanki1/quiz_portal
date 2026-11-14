<template>
  <nav>
    <div class="nav-brand">SlotWise</div>
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

const path = window.location.pathname
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
  gap: 16px;
  padding: 12px 24px;
  background-color: #1e3a5f;
  color: #fff;
}
.nav-brand {
  font-weight: 700;
  font-size: 18px;
  color: #93c5fd;
  white-space: nowrap;
}
.nav-links {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  flex-wrap: wrap;
}
a {
  color: #e2e8f0;
  text-decoration: none;
  font-size: 14px;
}
a:hover {
  color: #fff;
  text-decoration: underline;
}
.logout-btn {
  background: #b91c1c;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.logout-btn:hover {
  background: #991b1b;
}
</style>
