# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: unaryposts.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10unaryposts.proto\x12\nunaryposts\"$\n\x06\x43reate\x12\x0c\n\x04user\x18\x01 \x01(\t\x12\x0c\n\x04text\x18\x02 \x01(\t\"\"\n\x0fMessageResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\"0\n\x06Update\x12\x0c\n\x04user\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\x05\x12\x0c\n\x04text\x18\x03 \x01(\t\"\"\n\x06\x44\x65lete\x12\x0c\n\x04user\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\x05\"\x11\n\x03Get\x12\n\n\x02id\x18\x01 \x01(\x05\"\x16\n\x06GetAll\x12\x0c\n\x04user\x18\x01 \x01(\t\"-\n\x0cPostResponse\x12\x0f\n\x07message\x18\x01 \x01(\t\x12\x0c\n\x04user\x18\x02 \x01(\t\"!\n\x05Posts\x12\n\n\x02id\x18\x01 \x01(\x05\x12\x0c\n\x04text\x18\x02 \x01(\t\"1\n\rPostsResponse\x12 \n\x05posts\x18\x01 \x03(\x0b\x32\x11.unaryposts.Posts2\xc9\x02\n\nUnaryPosts\x12@\n\x0b\x63reate_post\x12\x12.unaryposts.Create\x1a\x1b.unaryposts.MessageResponse\"\x00\x12@\n\x0bupdate_post\x12\x12.unaryposts.Update\x1a\x1b.unaryposts.MessageResponse\"\x00\x12@\n\x0b\x64\x65lete_post\x12\x12.unaryposts.Delete\x1a\x1b.unaryposts.MessageResponse\"\x00\x12\x37\n\x08get_post\x12\x0f.unaryposts.Get\x1a\x18.unaryposts.PostResponse\"\x00\x12<\n\tget_posts\x12\x12.unaryposts.GetAll\x1a\x19.unaryposts.PostsResponse\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'unaryposts_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_CREATE']._serialized_start=32
  _globals['_CREATE']._serialized_end=68
  _globals['_MESSAGERESPONSE']._serialized_start=70
  _globals['_MESSAGERESPONSE']._serialized_end=104
  _globals['_UPDATE']._serialized_start=106
  _globals['_UPDATE']._serialized_end=154
  _globals['_DELETE']._serialized_start=156
  _globals['_DELETE']._serialized_end=190
  _globals['_GET']._serialized_start=192
  _globals['_GET']._serialized_end=209
  _globals['_GETALL']._serialized_start=211
  _globals['_GETALL']._serialized_end=233
  _globals['_POSTRESPONSE']._serialized_start=235
  _globals['_POSTRESPONSE']._serialized_end=280
  _globals['_POSTS']._serialized_start=282
  _globals['_POSTS']._serialized_end=315
  _globals['_POSTSRESPONSE']._serialized_start=317
  _globals['_POSTSRESPONSE']._serialized_end=366
  _globals['_UNARYPOSTS']._serialized_start=369
  _globals['_UNARYPOSTS']._serialized_end=698
# @@protoc_insertion_point(module_scope)
