// src/main.rs

// ======================================= EXAMPLE 1 =======================================
// This example enables the use of definitions inside a lib.rs file

use std::io;
// use student_package; // if the teacher wants to use the hidden lib

fn double(x: i32) -> i32 {
    x * 2
}

fn main() {
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let n: i32 = input.trim().parse().unwrap();
    // let n = student_package::__aux(); // if the teacher wants to use the hidden lib instead

    println!("{}", double(n));
}

// ======================================= EXAMPLE 2 (RECOMMENDED) =======================================
// This example is brought from https://github.com/erick12m/RPL-3.0-demo

// it is more flexible since the teacher can use any filename for the module they want, they just have to use mod instead of use, as if defining the module itself. The imported file does not need to define a `pub mod`, just to define public functions or structs.

// This might also allow the teacher to use the student_package (meaning, to use a lib.rs file) if they also want to, if they would like to make the main.rs file read only or hidden for the student; or for some other reason.

use std::io;
mod caesar_cipher;

fn main() {
    let mut user_input = String::new();
    io::stdin()
        .read_line(&mut user_input)
        .expect("Failed to read line");

    let user_input = user_input.trim();

    let mut shift = caesar_cipher::CaesarCipher::new(user_input.len() as i32);
    let encrypted = shift.encrypt(&user_input);
    println!("{}", encrypted);
}
