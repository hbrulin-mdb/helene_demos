db.history.aggregate([
  { $sort: { date_etat: 1 } },
  { 
    $merge: {
      into: "train_status_ordered",  
      on: "_id",                     
      whenMatched: "replace",        
      whenNotMatched: "insert"       
    }
  }
]);
