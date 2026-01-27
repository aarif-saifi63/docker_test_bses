import React from 'react'

import englishIcon from "../../assets/english.svg";
import hindiIcon from "../../assets/hindi.svg";

import newConsumer from "../../assets/new-consumer.svg";
import registeredConsumers from "../../assets/registered-consumers.svg";


const ButtonIcon = ({btn}) => {
    // console.log("[DEBUG] Button: ", btn);
  if(btn.includes("English")) {
    return (
      <img src={englishIcon} className="w-[30px]" alt="Language Icon" />
    )
  }else if(btn.includes("हिंदी")) {
    return (
      <img src={hindiIcon} className="w-[30px]" alt="Language Icon" />
    )
 }
    else if(btn.includes("New Consumer / नया उपभोक्ता") || btn.includes("नया एप्लिकेशन उपयोगकर्ता")) {
        return (
        <img src={newConsumer} className="w-[45px]" alt="New Consumer Icon" />

        )
    } else if(btn.includes("Registered Consumer / पंजीकृत उपभोक्ता") || btn.includes("पंजीकृत उपभोक्ता")) {
        return (
        <img src={registeredConsumers} className="w-[45px]" alt="Registered Consumer Icon" />
        )
    }
 else return null
}

export default ButtonIcon