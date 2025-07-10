// src/main.rs

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
