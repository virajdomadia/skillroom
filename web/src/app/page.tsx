import { Header } from "@/components/landing/Header";
import { Hero } from "@/components/landing/Hero";
import { Courses } from "@/components/landing/Courses";
import { Teach } from "@/components/landing/Teach";
import { Pricing } from "@/components/landing/Pricing";
import { Cta } from "@/components/landing/Cta";
import { Footer } from "@/components/landing/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Courses />
        <Teach />
        <Pricing />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
