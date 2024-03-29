import matplotlib.pyplot as plt
import os
import re
import shutil
import string
import tensorflow as tf
import time
from termcolor import cprint

from tensorflow.keras import layers
from tensorflow.keras import losses
print(tf.__version__)

time.sleep (0.5)
cprint('=======', "blue")
print('IMDB Classification AI')
print('By Dirk & Niels')
cprint('=======', "blue")
time.sleep(1)

if not os.path.isdir('aclImdb'):
    cprint("IMDB Database not found, downloading form ai.stanford.edu...", "yellow")
    # Download dataset
    url = "https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"
    dataset = tf.keras.utils.get_file("aclImdb_v1", url,untar=True, cache_dir='.', cache_subdir='')
    dataset_dir = os.path.join(os.path.dirname(dataset), 'aclImdb')
else:
    cprint('Dataset already present! Using ./aclImdb', "green")
    dataset_dir = './aclImdb'

train_dir = os.path.join(dataset_dir, 'train')

if os.path.isdir(os.path.join(train_dir, 'unsup')):
    cprint('Deleting unsup class reviews...', "yellow")
    shutil.rmtree(os.path.join(train_dir, 'unsup'))
    cprint('Done!', "green")

cprint('Creating training dataset...', "yellow")
batch_size = 32
seed = 42

raw_train_ds = tf.keras.utils.text_dataset_from_directory(
    'aclImdb/train', 
    batch_size=batch_size, 
    validation_split=0.2, 
    subset='training', 
    seed=seed)

cprint("Label 0 is " + str(raw_train_ds.class_names[0]), 'yellow')
cprint("Label 1 is " + str(raw_train_ds.class_names[1]), 'yellow')

time.sleep(0.5)

cprint('Creating validation dataset...', "yellow")
raw_val_ds = tf.keras.utils.text_dataset_from_directory(
    'aclImdb/train', 
    batch_size=batch_size, 
    validation_split=0.2, 
    subset='validation', 
    seed=seed)

cprint('Creating test dataset...', "yellow")
raw_test_ds = tf.keras.utils.text_dataset_from_directory(
    'aclImdb/test', 
    batch_size=batch_size)

def cleanup(input_data):
  stripped_html = tf.strings.regex_replace(tf.strings.lower(input_data), '<br />', ' ')
  return tf.strings.regex_replace(stripped_html, '[%s]' % re.escape(string.punctuation),'')

# begin model

vectorize_layer = layers.TextVectorization(
    standardize=cleanup,
    max_tokens=10000,
    output_mode='int',
    output_sequence_length=250)

# adapt vectorize layer 
vectorize_layer.adapt(raw_train_ds.map(lambda x, y: x))

def vectorize(text, label):
  text = tf.expand_dims(text, -1)
  return vectorize_layer(text), label

# text_batch, label_batch = next(iter(raw_train_ds))
# fr, fl = text_batch[0], label_batch[0]
# print("Review:\n    ", cleanup(fr))
# print("Label:\n", raw_train_ds.class_names[fl])
# print("Vectorized:\n", vectorize_text(fr, fl))

for x in range (0, 50):
    print(str(x) + " ---> ", vectorize_layer.get_vocabulary()[x])

#AUTOTUNE
AUTOTUNE = tf.data.AUTOTUNE
train_ds = raw_train_ds.map(vectorize).cache().prefetch(buffer_size=AUTOTUNE)
val_ds = raw_val_ds.map(vectorize).cache().prefetch(buffer_size=AUTOTUNE)
test_ds = raw_test_ds.map(vectorize).cache().prefetch(buffer_size=AUTOTUNE)


# MODEL!!!!!!!!!!!!

embedding_dim = 16
max_features = 10000
sequence_length = 250

model = tf.keras.Sequential([
  layers.Embedding(max_features + 1, embedding_dim),
  layers.Dropout(0.2),
  layers.GlobalAveragePooling1D(),
  layers.Dropout(0.2),
  layers.Dense(1)])

# model.summary()

model.compile(loss=losses.BinaryCrossentropy(from_logits=True),
              optimizer='adam',
              metrics=tf.metrics.BinaryAccuracy(threshold=0.0))


epochs = 25
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=epochs)

loss, accuracy = model.evaluate(test_ds)

print("Loss: ", loss)
print("Accuracy: ", accuracy)

history_dict = history.history
history_dict.keys()

acc = history_dict['binary_accuracy']
val_acc = history_dict['val_binary_accuracy']
loss = history_dict['loss']
val_loss = history_dict['val_loss']

epochs = range(1, len(acc) + 1)

# "bo" is for "blue dot"
plt.plot(epochs, loss, 'bo', label='Training loss')
# b is for "solid blue line"
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

plt.show()

plt.plot(epochs, acc, 'bo', label='Training acc')
plt.plot(epochs, val_acc, 'b', label='Validation acc')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend(loc='lower right')

plt.show()

export_model = tf.keras.Sequential([
  vectorize_layer,
  model,
  layers.Activation('sigmoid')
])

export_model.compile(
    loss=losses.BinaryCrossentropy(from_logits=False), optimizer="adam", metrics=['accuracy']
)

# Test it with `raw_test_ds`, which yields raw strings
loss, accuracy = export_model.evaluate(raw_test_ds)
print(accuracy)


cprint('Examples:', 'blue')
examples = [
  "The movie was great!",
  "The movie was okay.",
  "The movie was terrible..."
]
print(export_model.predict(examples))

# while 1:
#     cprint("Prompt:", "blue")
#     prompt = input()
#     cprint("Indelen....", "yellow")
#     print(export_model.predict([prompt]))

reviews = [
  "The movie was great!",
  "The movie was okay.",
  "The movie was terrible...",
  "I really enjoyed watching this,  I would definitely watch it again!",
  "Worst one so far, not a good experience. The music was good though",
  "In some bizarre way, this film just clicked for me...",
  "Visually this film is amazing in every way, the amount of detail and wonderful CGI is just pure eye candy. I loved the 3D, although it wasn't quite necessary,but hey, 3D is the standard these days for films in cinema. Overall, I do not think in my own humble and honest opinion that this move deserves the hate from the critics. Most movie goers, people I know who have seen the film, liked it. It is not a masterpiece. Long way from that. It is not an Oscarwinning film by no means. It's just a really fun film to watch.",
  "A film that utterly lacked any substance. There was promise at the beginning with a great opening introducing us to the anti-heroes which was awesome. And then.... Nothing? Stranded such a talented cast fighting comical looking goons and an anti-climax of a villian. The two stars are for Viola Davis and Margot Robbie who give their roles everything. Every other character is disposable and forgettable. And Jared Leto as the Joker? Lets say no more.",
  "Is this movie terrible? Absolutely not. Is this movie great? Absolutely not. I always heard from people that they either HATED or LOVED this movie. And for me it was neither. The audience for this film is served with a classic action movie/comic book. The world is in danger! There must be a solution! Although there are bumps between the characters along the way, eventually, we'll solve the problem",
  "The interesting twist is *supposed* to be that instead of classic superheroes, we have bad guys. To that I say 'so what?'. The movie didn't really establish why I should care about much of what was going on on screen—it was all just classic popcorn movie action and sequences that were occasionally broken up by half-attempts at character development."
]

print(export_model.predict(reviews))
print([0.47739536])
print([0.40126287])
print(reviews)

chinees = [
  "Had running buffet the other day after a trade show. Food was good. Price was low. We ate faster than it could refill the buffet. Had enough to eat in the end though. Parking: There is a parking garage nearby!",
  "Eaten once during winter. It was unpleasantly cold and the dishes were bland and heated up quickly. I didn't like the food. Not even when I once ate at people's houses who always took away here",
  "It is very cosy here.  The meal is fine. The service very obliging despite it being very busy now.",
  "I ordered food from them and when I got home there were black hairs in the food.  So no not recommended.",
  "Just got 'Chinese' here for the first time. Large portions, prices not crazy expensive. Then again, I found the peanut sauce really tasteless and very greasy, almost had to throw away all the food just to avoid eating dry rice. If you are used to regular Chinese, I will therefore not recommend it."
]
cprint("chinees:", "blue")
print(export_model.predict(chinees))
print(chinees)