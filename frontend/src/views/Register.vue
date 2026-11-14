<template>
    <Navbar />
    <div>
        <h1>Register</h1>
    </div>
    <div v-if="message">
        <p>{{ message }}</p>
    </div>
    <div v-if="error">
        <p>{{ error }}</p>
    </div>
    <form @submit.prevent="portalRegister">
        <input type="text" v-model="username" placeholder="Username">
        <input type="email" v-model="email" placeholder="Email">
        <input type="password" v-model="password" placeholder="Password">
        <select v-model="role">
            <option value="user">User</option>
        </select>
        <button type="submit">Register</button>
    </form>
</template>

<script setup>
import Navbar from './components/Navbar.vue'
import axios from 'axios'
import { ref } from 'vue'
const username = ref('')
const email = ref('')
const password = ref('')
const role = ref('user')
const message = ref('')
const error = ref('')
const portalRegister = async () =>{
    try{
        const responce = await axios.post(
            "http://127.0.0.1:5000/register_new_student",
            {
                username:username.value,
                email:email.value,
                password:password.value,
                role:role.value
            }
        )
        message.value = responce.data.message
        error.value = ''
    } catch(err){
        error.value = err.response && err.response.data ? err.response.data.message : 'Register failed'
    }
}

</script>

<style scoped>
</style>